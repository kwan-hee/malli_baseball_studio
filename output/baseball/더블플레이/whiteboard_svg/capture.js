/**
 * Puppeteer 프레임 캡처 — index.html 화이트보드 애니메이션 → PNG 시퀀스
 * 사용: node capture.js
 * 출력: frames/frame_0001.png ~ frame_NNNN.png (30fps)
 *
 * 별도 HTTP 서버 불필요 — puppeteer가 file:// 로 직접 로드
 */
const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

// ============================================================
// CONFIG
// ============================================================
const FPS = 30;
const WIDTH = 1526;
const HEIGHT = 1017;
const FRAMES_DIR = path.join(__dirname, 'frames');

// 타이밍 (index.html CONFIG과 맞춤)
const DRAW_A_SEC = 3.5;
const PAUSE_AFTER_A = 0.8;
const ERASE_SEC = 2.5;
const PAUSE_AFTER_ERASE = 0.3;
const DRAW_B_SEC = 3.5;
const HAND_IN_OUT = 0.4;

// 전체 예상 길이 (여유 포함)
const TOTAL_SEC = DRAW_A_SEC + PAUSE_AFTER_A + ERASE_SEC + PAUSE_AFTER_ERASE + DRAW_B_SEC + HAND_IN_OUT * 4 + 1;
const TOTAL_FRAMES = Math.ceil(TOTAL_SEC * FPS);

// ============================================================
// MAIN
// ============================================================
(async () => {
  // frames 폴더 정리
  if (fs.existsSync(FRAMES_DIR)) {
    fs.readdirSync(FRAMES_DIR).forEach(f => fs.unlinkSync(path.join(FRAMES_DIR, f)));
  } else {
    fs.mkdirSync(FRAMES_DIR);
  }

  console.log(`Launching browser (${WIDTH}x${HEIGHT}, ${FPS}fps, ~${TOTAL_FRAMES} frames)...`);

  const browser = await puppeteer.launch({
    headless: true,
    args: [`--window-size=${WIDTH},${HEIGHT}`],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: WIDTH, height: HEIGHT });

  // index.html 로드
  const htmlPath = path.join(__dirname, 'index.html');
  await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle0' });
  console.log('Page loaded');

  // requestAnimationFrame을 수동 제어하기 위해 시간을 가로챔
  // 실시간 대신 프레임 단위로 시간을 진행
  await page.evaluate(() => {
    // 실제 rAF 백업
    window._realRAF = window.requestAnimationFrame;
    window._rafQueue = [];
    window._fakeTime = performance.now();

    // rAF를 큐에 쌓기만 하고 실행하지 않음
    window.requestAnimationFrame = (cb) => {
      window._rafQueue.push(cb);
      return window._rafQueue.length;
    };

    // performance.now() 가로채기
    window._origPerfNow = performance.now.bind(performance);
    performance.now = () => window._fakeTime;
  });

  // Full sequence 시작
  await page.evaluate(() => {
    CONFIG.DRAW_DURATION_SEC = 3.5;
    CONFIG.ERASE_DURATION_SEC = 2.5;
    CONFIG.HAND_IN_OUT_SEC = 0.4;
    runFull();
  });

  console.log('Animation started, capturing frames...');

  const frameDuration = 1000 / FPS; // ms per frame
  let frameNum = 0;
  let idleCount = 0;

  while (frameNum < TOTAL_FRAMES + FPS * 2) { // 여유 2초
    frameNum++;

    // 가짜 시간 진행
    await page.evaluate((dt) => {
      window._fakeTime += dt;
      // 큐에 쌓인 rAF 콜백 모두 실행
      const queue = window._rafQueue.splice(0);
      queue.forEach(cb => {
        try { cb(window._fakeTime); } catch(e) {}
      });
    }, frameDuration);

    // 스크린샷 캡처
    const padded = String(frameNum).padStart(4, '0');
    const framePath = path.join(FRAMES_DIR, `frame_${padded}.png`);
    await page.screenshot({ path: framePath, type: 'png', omitBackground: true });

    // 진행 표시 (10프레임마다)
    if (frameNum % 10 === 0) {
      const phase = await page.evaluate(() => document.getElementById('phase').textContent);
      process.stdout.write(`\r  Frame ${frameNum}/${TOTAL_FRAMES} | Phase: ${phase}    `);

      // idle 상태가 오래 지속되면 (draw_b 완료 후) 종료
      if (phase === 'idle' && frameNum > FPS * 3) {
        idleCount++;
        if (idleCount > 3) {
          console.log(`\n  Animation complete at frame ${frameNum}`);
          break;
        }
      } else {
        idleCount = 0;
      }
    }
  }

  console.log(`\nCaptured ${frameNum} frames to ${FRAMES_DIR}/`);

  await browser.close();

  // ffmpeg 합성 안내
  console.log('\n=== Next: ffmpeg 합성 ===');
  console.log(`ffmpeg -framerate ${FPS} -i frames/frame_%04d.png -c:v libx264 -pix_fmt yuv420p transition.mp4`);
  console.log('(투명 배경 합성용):');
  console.log(`ffmpeg -framerate ${FPS} -i frames/frame_%04d.png -c:v prores_ks -pix_fmt yuva444p10le transition.mov`);
})();
