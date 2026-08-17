#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断：流式 VAD 原始输出格式实测。把 p004 前 20s 按 0.5s 块喂给
FsmnVADStreaming，逐块打印 value 原始值，确认 [start,-1]/[-1,end] 的
确切语义与坐标系（相对 chunk 还是全局流）。"""
import sys, time
import numpy as np
import soundfile as sf
sys.path.insert(0, "/Volumes/Backups/scribe")
from funasr import AutoModel

VAD_DIR = "/Volumes/Backups/scribe/models/speech_fsmn_vad"
wav, sr = sf.read("/Volumes/Backups/scribe/data/test/p004_126s.wav")
if wav.ndim > 1: wav = wav.mean(axis=1)
wav = wav[:int(20 * sr)].astype(np.float32)

vad = AutoModel(model=VAD_DIR, trust_remote_code=True, device="cpu",
                disable_update=True, disable_pbar=True)

cache = {}
CHUNK = int(sr * 0.5)
offset_ms = 0
for i in range(0, len(wav), CHUNK):
    chunk = wav[i:i + CHUNK]
    is_final = (i + CHUNK >= len(wav))
    t0 = time.time()
    res = vad.generate(input=chunk, cache=cache, is_final=is_final,
                       chunk_size=60, disable_pbar=True)
    val = res[0].get("value") if res else None
    if val:
        print(f"块 {i//CHUNK:2d} (offset={offset_ms:5d}ms): value={val}", flush=True)
    offset_ms += int(round(len(chunk) / sr * 1000))
print("完成，总时长", offset_ms, "ms")
