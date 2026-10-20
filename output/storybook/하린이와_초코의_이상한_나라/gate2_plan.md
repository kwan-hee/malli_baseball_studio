# 하린이와 초코의 이상한 나라 — 2차 게이트 자료 (2026-10-20)

설계: docs/superpowers/specs/2026-10-20-lecture-sample-alice-design.md

## 캐릭터 시트 (생성 완료, QC 통과)

- characters/harin_sheet.png — 1차 통과
- characters/choco_sheet.png — v2 통과 (v1은 놀람 표정에서 귀가 뾰족하게 서고 털색이 옅어 재생성, choco_sheet_v1.png 보관)
- characters/alice_sheet.png — 1차 통과 (민트 원피스·노란 리본, 디즈니 요소 없음)
- 엄마(s10 한 장면)는 시트 없이 images/portraits/mom.png 를 참조로 첨부

## 한국어 대본 (make_narration.py SCENES 로 들어감)

| 씬 | 대본 |
|---|---|
| s01 | 까만 밤, 하린이는 초코와 함께 침대에 누웠어요. 오늘 밤 그림책은 이상한 나라의 앨리스예요. 하린이가 하아암, 하품을 하는 순간이었어요. 그림책 속 토끼 굴이 반짝반짝 빛나기 시작했어요. 초코가 꼬리를 살랑 흔들더니, 굴 속으로 쏙 들어가 버렸어요! |
| s02 | 초코야, 기다려! 같이 가자! 하린이도 초코를 따라 굴 속으로 들어갔어요. 둥실, 둥실. 하린이와 초코는 깃털처럼 천천히 내려갔어요. 찻잔도, 시계도, 그림책도 함께 둥둥 떠다녔어요. 하나도 무섭지 않았어요. 초코가 옆에 있었으니까요. |
| s03 | 도착한 곳은 아주 작은 문이 있는 방이었어요. 탁자 위에는 나를 마셔요, 라고 적힌 병이 있었어요. 하린이와 초코가 한 모금씩 마시자, 둘 다 쏙 작아졌어요. 그때 금빛 머리의 여자아이가 다가왔어요. 안녕, 나는 앨리스야. 너희도 길을 잃었구나? |
| s04 | 셋은 나란히 숲길을 걸었어요. 나뭇가지 위에 커다란 웃음 하나가 둥실 떠올랐어요. 히히, 집에 가고 싶니? 줄무늬 체셔 고양이였어요. 집으로 가는 문은 여왕님 정원 너머에 있지. 고양이는 웃음만 남기고 스르르 사라졌어요. |
| s05 | 숲 속 빈터에서는 신나는 차 모임이 열리고 있었어요. 커다란 모자를 쓴 모자 장수가 외쳤어요. 생일 아닌 날, 축하해! 하린이도 초코도 함께 노래를 불렀어요. 모자 장수는 시계 모양 열쇠를 건네주었어요. 이 열쇠가 집으로 가는 문을 열어 줄 거야. 초코야, 같이 가자! |
| s06 | 드디어 하트 여왕님의 정원에 왔어요. 카드 병정들이 하얀 장미를 빨갛게 칠하고 있었어요. 그런데 초코가 꼬리를 흔들다가, 물감 통을 엎어 버렸어요. 하얀 길이 온통 빨갛게 물들었어요. 여왕님이 발을 동동 구르며 소리쳤어요. 누가 내 정원을 이렇게 만들었느냐! |
| s07 | 카드 병정들이 허둥지둥 쫓아오기 시작했어요. 얘들아, 달려! 앨리스가 외쳤어요. 초코야, 같이 가자! 셋은 장미 덤불 사이로 힘껏 달렸어요. 그때 시원한 바람이 휘이잉 불어왔어요. 카드 병정들이 와르르 흩어져 하늘로 날아갔어요. 하린이와 앨리스는 깔깔 웃었어요. |
| s08 | 정원 끝에 작고 둥근 문이 있었어요. 하린이가 시계 열쇠를 넣고 돌리자, 철컥 문이 열렸어요. 문 너머로 따뜻한 빛이 쏟아졌어요. 앨리스, 같이 가지 않을래? 나는 내 집으로 가야 해. 하지만 또 놀러 와. 꿈에서 기다릴게. 하린이와 앨리스는 서로를 꼭 안아 주었어요. |
| s09 | 눈을 떠 보니, 하린이는 자기 침대에 누워 있었어요. 초코도 옆에서 새근새근 자고 있었어요. 모두 꿈이었을까요? 그런데 베개 옆에 작은 하트 카드 한 장이 놓여 있었어요. 하린이는 카드를 꼭 쥐고 살며시 웃었어요. |
| s10 | 엄마가 들어와 이불을 포근히 덮어 주었어요. 엄마, 나 내일 밤에도 앨리스 만나는 꿈 꿀래. 그래, 초코랑 같이 다녀오렴. 낯선 곳에서도 함께라면, 언제나 길을 찾을 수 있어요. 하린이는 초코를 꼭 안고 스르르 잠이 들었어요. 잘 자요, 우리 친구들. |

## English script (make_narration_en.py)

| Scene | Script |
|---|---|
| s01 | It was a dark, quiet night. Harin snuggled into bed with her puppy, Choco. Tonight's picture book was Alice in Wonderland. Just as Harin let out a big, sleepy yawn, the rabbit hole in the book began to sparkle. Choco wagged his tail, and whoosh! He hopped right into the hole! |
| s02 | Choco, wait for me! Let's go together! Harin followed Choco down the hole. Down, down they floated, as gently as feathers. Teacups, clocks, and storybooks drifted all around them. Harin wasn't scared at all, because Choco was right beside her. |
| s03 | They landed in a room with a very tiny door. On the table stood a little bottle that said, Drink Me. Harin and Choco each took a sip, and they shrank down small. Then a girl with golden hair walked over. Hello, I'm Alice. Are you lost too? |
| s04 | The three friends walked side by side down a forest path. On a tree branch, a big smile appeared out of nowhere. Hee hee, do you want to go home? It was the striped Cheshire Cat. The door home is past the Queen's garden. Then the cat faded away, leaving only its smile. |
| s05 | In a clearing, a merry tea party was going on. The Hatter, in his enormous hat, called out, Happy unbirthday! Harin and Choco sang along. The Hatter handed them a key shaped like a clock. This key will open the door home. Choco, let's go together! |
| s06 | At last, they reached the Queen of Hearts' garden. Card soldiers were painting white roses red. But Choco wagged his tail and knocked over a paint pot! The whole white path turned bright red. The Queen stamped her feet. Who made a mess of my garden? |
| s07 | The card soldiers came hurrying after them. Run! shouted Alice. Choco, let's go together! The three of them dashed between the rose bushes. Just then, a cool breeze came whooshing by. The card soldiers tumbled and fluttered up into the sky. Harin and Alice giggled and giggled. |
| s08 | At the end of the garden was a small round door. Harin turned the clock key, and click! The door swung open. Warm light poured through. Alice, won't you come with us? I have to go to my own home. But come and visit again. I'll wait for you in your dreams. Harin and Alice gave each other a big hug. |
| s09 | When Harin opened her eyes, she was back in her own bed. Choco was sleeping softly beside her. Was it all a dream? But next to her pillow lay a tiny heart card. Harin held it tight and smiled. |
| s10 | Mom came in and tucked the blanket around her. Mom, I want to dream about Alice again tomorrow night. Of course, sweetheart. Take Choco with you. Even in a strange place, when we're together, we can always find our way. Harin hugged Choco close and drifted off to sleep. Good night, my friends. |

## 씬 점수표 + 배정표 (13_SCENE_SCORING: motion 7+ AND importance 85+)

| 씬 | 내용 | emotion | motion | importance | 배정 |
|---|---|---|---|---|---|
| s01 | 침대, 그림책 굴 반짝, 초코 뛰어듦 | 6 | 5 | 80 | 이미지 + Ken Burns |
| s02 | 굴 아래로 둥실둥실 낙하 | 7 | 9 | 85 | ✅ 영상 — Veo 3.1 Fast |
| s03 | 작아지는 병, 앨리스 만남 | 7 | 5 | 85 | 이미지 + Ken Burns |
| s04 | 체셔 고양이 웃음만 남기고 사라짐 | 6 | 4 | 75 | 이미지 + Ken Burns |
| s05 | 모자 장수 차 모임, 시계 열쇠 | 8 | 5 | 80 | 이미지 + Ken Burns |
| s06 | 초코가 물감 통 엎음, 여왕 발 구름 | 8 | 6 | 85 | 이미지 + Ken Burns |
| s07 | 탈출, 카드 병정 바람에 흩어짐 (절정) | 9 | 10 | 95 | ✅ 영상 — Veo 3.1 Fast |
| s08 | 시계 열쇠로 문 열기, 앨리스와 작별 | 9 | 4 | 90 | 이미지 + Ken Burns |
| s09 | 침대에서 깸, 하트 카드 | 7 | 2 | 80 | 이미지 + Ken Burns |
| s10 | 엄마 이불, 잠듦 | 8 | 2 | 85 | 이미지 + Ken Burns |

- 영상 2개(s02, s07). 둘 다 Veo 3.1 Fast (context-notes: 동화 클립은 사용자 선택으로 Fast 유지). 폴백 체인은 gen_clips_veo.py 그대로.
- s06은 motion 6으로 영상 제외. s08은 importance 90이지만 정적 장면이라 제외.

## 승인 후 자동 진행 순서

1. gen_images.py — 씬 10장 (시트 3장 + s10은 엄마 사진 첨부), 10장 전수 QC
2. gen_clips_veo.py — s02, s07
3. make_narration.py (한) / make_narration_en.py (영) — 각 단일 호출
4. make_bgm.py → compose.py (한) / compose_en.py (영) → 프레임 검증
5. 캐릭터 탄생 비교 이미지 2장
6. 전자책 EPUB + 단일 HTML → epubcheck, 브라우저 동작 확인
