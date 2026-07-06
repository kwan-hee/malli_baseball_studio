# 08. ffmpeg 명령 모음

자동 조립·후처리용 표준 명령. 경로는 예시 — 실제 편명으로 치환.

## 이미지 → Ken Burns 줌 클립

```
ffmpeg -loop 1 -i 01_scene.png -vf "zoompan=z='min(zoom+0.0008,1.2)':d=900:s=1920x1080:fps=30" -t 30 -pix_fmt yuv420p scene01.mp4
```

- `0.0008` 줌 속도, `1.2` 최대 배율, `d=900` = 30초x30fps
- CapCut에서 할 경우 docs/02_VIDEO_POLICY.md 의 common_keyframes 방식 사용

## 클립 이어붙이기

```
ffmpeg -f concat -safe 0 -i list.txt -c copy full.mp4
```

list.txt 형식:
```
file 'scene01.mp4'
file 'scene02.mp4'
```

## 나레이션 + BGM 믹싱 (BGM -15dB)

```
ffmpeg -i narration.mp3 -i bgm.mp3 -filter_complex "[1:a]volume=-15dB[bg];[0:a][bg]amix=inputs=2:duration=first" mixed.mp3
```

## 영상 + 오디오 합치기

```
ffmpeg -i full.mp4 -i mixed.mp3 -c:v copy -c:a aac -shortest final.mp4
```

## 썸네일 텍스트 합성 (drawtext)

```
ffmpeg -i thumb_bg.png -vf "drawtext=fontfile='C\:/Windows/Fonts/malgunbd.ttf':text='보크가 뭐길래?':fontsize=120:fontcolor=white:borderw=8:bordercolor=black:x=(w-text_w)/2:y=h-300" thumbnail.png
```

## 쇼츠 변환 (1080x1920 크롭)

```
ffmpeg -i final.mp4 -vf "crop=ih*9/16:ih,scale=1080:1920" shorts.mp4
```

## 최종 검수

- 렌더 후 반드시 재생 확인 (첫 5초, 중간, 끝)
- 오디오 레벨 확인: `ffmpeg -i final.mp4 -af loudnorm=print_format=summary -f null -` → -14 LUFS 내외
