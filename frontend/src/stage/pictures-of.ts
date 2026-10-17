/**
 * Every picture a theatre has put on the page (its `<img>`s and its drawings' `<image>`s),
 * loaded and decoded, or `cap` ms: what a cover over a theatre waits on before it lifts, so the
 * theatre is never seen half drawn (its stage paints its dark ground at once, its pictures as
 * they come), and the decoding is done under the cover, not in its lift.
 *
 * A theatre whose code is still on its way has put nothing on the page yet: it is waited for,
 * within the same cap, before its pictures are counted.
 */
export async function picturesOf(el: HTMLElement, cap = 4000): Promise<void> {
  const until = Date.now() + cap;
  const pictures = () => el.querySelectorAll('img, image').length > 0;
  while (!pictures() && Date.now() < until)
    await new Promise((done) => setTimeout(done, 100));
  // a theatre places its pictures over its next renders (the stage measures first, the scene
  // then describes its backdrop): two frames, and they are all on the page
  await new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)));
  const srcs = new Set<string>();
  el.querySelectorAll('img').forEach((img) => img.currentSrc && srcs.add(img.currentSrc));
  el.querySelectorAll('image').forEach((img) => {
    const href = img.getAttribute('href');
    if (href) srcs.add(href);
  });
  const all = [...srcs].map((src) => {
    const img = new Image();
    img.src = src;
    return img.decode().catch(() => {});
  });
  await Promise.race([
    Promise.all(all),
    new Promise((done) => setTimeout(done, Math.max(0, until - Date.now()))),
  ]);
}
