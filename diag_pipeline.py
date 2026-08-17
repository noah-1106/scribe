#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断：完整实时管线离线复现（不经网络），逐步定位哪一环不吐句。

复现 test_live.py 的输入路径：
  wav → 0.5s 一块 webm 编码 → ffmpeg_decode_block 解码 → LiveSession
逐步骤打印：解码采样数、VAD 闭合段、识别结果。"""
import base64, math, subprocess, sys, time
import numpy as np
import soundfile as sf
sys.path.insert(0, "/Volumes/Backups/scribe")

BASE = "/Volumes/Backups/scribe"
wav, sr = sf.read(f"{BASE}/data/test/p004_126s.wav")
if wav.ndim > 1: wav = wav.mean(axis=1)
wav = wav[:int(35 * sr)].astype(np.float32)

# 预编码（同 test_live.py）
block = int(sr * 0.5)
blocks = []
for i in range(math.ceil(len(wav) / block)):
    pcm16 = (wav[i*block:(i+1)*block] * 32767).astype("int16").tobytes()
    p = subprocess.run([f"{BASE}/bin/ffmpeg","-v","error","-f","s16le","-ar","16000","-ac","1",
                        "-i","pipe:0","-c:a","libopus","-f","webm","pipe:1"],
                       input=pcm16, capture_output=True)
    blocks.append(p.stdout)
print(f"[1] 预编码 {len(blocks)} 块", flush=True)

from funasr import AutoModel
from realtime import LiveSession, ffmpeg_decode_block

asr = AutoModel(model=f"{BASE}/models/SenseVoiceSmall", trust_remote_code=True,
                device="cpu", disable_update=True, disable_pbar=True)
vad = AutoModel(model=f"{BASE}/models/speech_fsmn_vad", trust_remote_code=True,
                device="cpu", disable_update=True, disable_pbar=True)
sess = LiveSession(asr, vad, False, lambda: None)

total_closed = 0
for i, raw in enumerate(blocks):
    sess.push_block(i, raw)
    closed = sess.drain()
    if i < 3 or closed or i % 10 == 0:
        print(f"[2] 块{i:2d}: 解码后缓冲 {sess.wav.size/sr:.1f}s, 闭合段 {closed}", flush=True)
    for seg in closed:
        total_closed += 1
        sent = sess.recognize(seg["start"], seg["end"])
        print(f"[3] 识别 [{seg['start']:.2f}->{seg['end']:.2f}]: {(sent or {}).get('text','<空>')[:40]}", flush=True)

print(f"[4] 流内闭合段总数: {total_closed}", flush=True)
rest = sess.vadstream.finish()
print(f"[5] finish 收口段: {rest}", flush=True)
for seg in rest:
    sent = sess.recognize(seg["start"], seg["end"])
    print(f"[6] 收口识别 [{seg['start']:.2f}->{seg['end']:.2f}]: {(sent or {}).get('text','<空>')[:50]}", flush=True)
