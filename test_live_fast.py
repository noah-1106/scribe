#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实时转录端到端测试（紧凑版）：推流 0.3s/块、总时长 18s、无 stop 后空等。
验证三件事：1) 句子实时到达（不是停止后才到）2) partial 到达 3) final 落盘。
"""
import asyncio, base64, json, math, subprocess, sys, time
import websockets, soundfile as sf

BASE = "/Volumes/Backups/scribe"
wav, sr = sf.read(f"{BASE}/data/test/p004_126s.wav")
if wav.ndim > 1: wav = wav.mean(axis=1)
wav = wav[:int(18*sr)]

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

PACE = 0.3  # 比真实 0.5s 快一点，压缩总时长

async def main():
    async with websockets.connect("ws://localhost:8399/ws/live", max_size=8*1024*1024) as ws:
        await ws.send(json.dumps({"type":"start","diarize":False}))
        results, partials = [], []
        t0 = time.time()

        async def recv_loop():
            async for raw in ws:
                m = json.loads(raw)
                el = time.time() - t0
                if m["type"] == "ready":
                    print(f"  [ready] t={el:.1f}s", flush=True)
                elif m["type"] == "sentence":
                    results.append((el, m))
                    print(f"  [句] t={el:5.1f}s [{m['start']:6.2f}->{m['end']:6.2f}] {m['text'][:40]}", flush=True)
                elif m["type"] == "partial":
                    partials.append((el, m))
                    print(f"  [暂] t={el:5.1f}s [{m['start']:6.2f}->{m['end']:6.2f}] {m['text'][:40]}", flush=True)
                elif m["type"] == "final":
                    print(f"  [final] t={el:.1f}s {m['n_sentences']} 句 {m['duration_s']}s", flush=True)
                    return
                elif m["type"] == "error":
                    print(f"  [error] t={el:.1f}s {m['message']}", flush=True)

        rt = asyncio.create_task(recv_loop())
        for i, b64 in enumerate(blocks):
            await ws.send(json.dumps({"type":"block","seq":i,"data":b64}))
            await asyncio.sleep(PACE)
        stop_at = time.time() - t0
        await ws.send(json.dumps({"type":"stop"}))
        try:
            await asyncio.wait_for(rt, timeout=25)
        except asyncio.TimeoutError:
            print("TIMEOUT waiting final", flush=True)
        print(f"\nstop@{stop_at:.1f}s | 定稿句 {len(results)}（停止前到达 {sum(1 for e,_ in results if e < stop_at)} 条）| partial {len(partials)}", flush=True)

asyncio.run(main())
