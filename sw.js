/* 스도쿠 무제한 퍼즐 - 오프라인 지원 서비스 워커
 * 페이지(HTML): 네트워크 우선 → 실패 시 저장본 (온라인이면 항상 최신)
 * 같은 출처의 정적 파일: 저장본 우선 → 없으면 네트워크
 * 다른 출처(광고 등): 관여하지 않음
 */
const CACHE = 'sudokuportal-v1';
const CORE = [
  '/', '/daily.html', '/level/easy.html', '/level/normal.html', '/level/hard.html', '/level/expert.html',
  '/guides/', '/manifest.json', '/icons/icon-192.png', '/icons/icon-512.png', '/favicon.ico', '/apple-touch-icon.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => Promise.all(CORE.map((url) => cache.add(url).catch(() => null))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  const isPage = req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html');
  if (isPage) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((cache) => cache.put(url.pathname, copy));
          }
          return res;
        })
        .catch(() => caches.match(url.pathname).then((hit) => hit || caches.match('/')))
    );
    return;
  }

  event.respondWith(
    caches.match(req).then((hit) => hit || fetch(req).then((res) => {
      if (res.ok) {
        const copy = res.clone();
        caches.open(CACHE).then((cache) => cache.put(req, copy));
      }
      return res;
    }))
  );
});
