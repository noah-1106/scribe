#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""说话人分离隔离验证：直接用 VAD 段做 CAM++ 嵌入 + 聚类，绕过 ASR 时间戳环节。

背景：测试音频是拼接的（zh/en/zh），ASR 对 48k 源文件的词级时间戳不可靠
（"Thecrowdtreescantohere" 这类乱句 + 时间戳超界），所以本测试
用 VAD 边界（可信）代替句子边界，验证 diarization 核心链路本身。
"""
import os
import numpy as np, soundfile as sf
from funasr import AutoModel
from diarize import label_speakers

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{BASE}/data/test/two_spk.wav"
mix, sr = sf.read(OUT)

vad = AutoModel(model=f"{BASE}/models/speech_fsmn_vad", trust_remote_code=True, device="cpu", disable_update=True)
sv = AutoModel(model=f"{BASE}/models/campplus_sv", trust_remote_code=True, device="cpu", disable_update=True)

segs = vad.generate(input=OUT)[0]["value"]
print(f"VAD 切出 {len(segs)} 段：", [(round(a/1000,2), round(b/1000,2)) for a, b in segs])

# 用 VAD 段当"句子"，标签用文字内容指代（前段 zh，中段 en，后段 zh）
names = ["zh", "en", "zh2"]
sents = [{"start": a/1000, "end": b/1000, "text": names[i]} for i, (a, b) in enumerate(segs)]
label_speakers(sents, mix, sr, sv)
for s in sents:
    print(f"[{s['start']:6.2f}→{s['end']:6.2f}] {s['speaker']}  (真实={s['text']})")

zh_labels = [s["speaker"] for s in sents if s["text"].startswith("zh")]
en_labels = [s["speaker"] for s in sents if s["text"] == "en"]
ok = len(set(zh_labels)) == 1 and len(set(en_labels)) == 1 and zh_labels[0] != en_labels[0]
print("\n判定：", "✅ 通过——zh/zh2 同人同标、en 异人异标" if ok else "❌ 未通过")
