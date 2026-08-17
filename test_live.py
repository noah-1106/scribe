#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实时转录端到端测试：把 p004 前 35s 按浏览器节奏（0.5s webm 块）推给 /ws/live。

与上一版的差别：解码 / 编码全部预先离线做好，推流阶段纯网络 + sleep，
避免 60s 工具超时被 ffmpeg 子进程拖爆。
"""
import asyncio, base64, json, math, os, subprocess, sys, time
import websockets, soundfile as sf

BASE = os.path.dirname(os.path.abspath(__file__))
wav, sr = sf.read(f"{BASE}/data/test/p004_126s.wav")
if wav.ndim > 1: wav = wav.mean(axis=1)
wav = wav[:int(35*sr)]

# 预先把 0.5s 一块的 webm 编码好（模拟 MediaRecorder 产物）
block = int(sr * 0.5)
nblocks = math.ceil(len(wav) / block)
blocks = []
for i in range(nblocks):
    pcm16 = (wav[i*block:(i+1)*block] * 32767).astype("int16").tobytes()
    p = subprocess.run([f"{BASE}/bin/ffmpeg","-v","error","-f","s16le","-ar","16000","-ac","1",
                        "-i","pipe:0","-c:a","libopus","-f","webm","pipe:1"],
                       input=pcm16, capture_output=True)
    blocks.append(base64.b64encode(p.stdout).decode())
print(f"预编码 {len(blocks)} 块完成", flush=True)

async def main():
    async with websockets.connect("ws://localhost:8399/ws/live", max_size=8*1024*1024) as ws:
        await ws.send(json.dumps({"type":"start","diarize":False}))
        results, partials = [], []
        t0 = time.time()

        async def recv_loop():
            async for raw in ws:
                m = json.loads(raw)
                if m["type"] == "sentence":
                    results.append(m)
                    print(f"  [句] [{m['start']:6.2f}->{m['end']:6.2f}] {m['text'][:40]}", flush=True)
                elif m["type"] == "partial":
                    partials.append(m)
                    print(f"  [暂] [{m['start']:6.2f}->{m['end']:6.2f}] {m['text'][:40]}", flush=True)
                elif m["type"] == "final":
                    print("  [final]", m["n_sentences"], "句", m["duration_s"], "s", flush=True)
                    return
                elif m["type"] == "error":
                    print("  [error]", m["message"], flush=True)

        rt = asyncio.create_task(recv_loop())
        for i, b64 in enumerate(blocks):
            await ws.send(json.dumps({"type":"block","seq":i,"data":b64}))
            elapsed = time.time()-t0
            if elapsed < (i+1)*0.5: await asyncio.sleep((i+1)*0.5-elapsed)
        await ws.send(json.dumps({"type":"stop"}))
        try: await asyncio.wait_for(rt, timeout=30)
        except asyncio.TimeoutError: print("TIMEOUT")
        print(f"\n总句子 {len(results)}, partial {len(partials)}, 耗时 {time.time()-t0:.1f}s", flush=True)

asyncio.run(main())
