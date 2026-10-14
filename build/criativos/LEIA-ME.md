# Criativos comerciais (HyperFrames)

Composições HyperFrames dos anúncios do portal. O HyperFrames usado é o do Dubra Frame
(`Dubra Frame - Gerador de video/ferramentas/hyperframes`, versão 0.8.81), sempre local: nunca
`init`, `publish`, `cloud` nem `lambda`.

## billboard/

Faixa acima da manchete da home (formato G1). `desktop/` desenha 970x250 e `mobile/` 320x100,
ambos renderizados em 2x.

Para refazer:

1. Copie para `desktop/assets/` e `mobile/assets/`: `gsap.min.js` (de
   `ferramentas/hyperframes/node_modules/gsap/dist/`) e `Montserrat-ExtraBold.ttf` e
   `Inter-SemiBold.ttf` (de `Dubra Frame - Gerador de video/app/fontes/`, OFL 1.1). Essa pasta não vai
   para o git.
2. Na pasta `ferramentas/hyperframes`, com `HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1
   HYPERFRAMES_NO_UPDATE_CHECK=1 HYPERFRAMES_SKIP_SKILLS=1 HYPERFRAMES_NO_AUTO_INSTALL=1`:
   - `npx --no-install hyperframes lint <pasta>`
   - `npx --no-install hyperframes snapshot <pasta> --at 2.3 --no-end --describe false` (no mobile, `--at 1.95`)
3. Converta o PNG do quadro final para WebP com qualidade 85:
   - `assets/images/anuncios/billboard.webp` (1940x500)
   - `assets/images/anuncios/billboard-mobile.webp` (640x200)
4. Versão animada (6 s, termina no quadro completo): renderize e recomprima sem áudio.
   - `npx --no-install hyperframes render <pasta> --format mp4 -q delivery -o <saida>.mp4`
   - `ffmpeg -i <saida>.mp4 -an -c:v libx264 -pix_fmt yuv420p -crf 26 -preset slow -movflags +faststart assets/images/anuncios/billboard.mp4`
   - `ffmpeg -i <saida>.mp4 -an -c:v libvpx-vp9 -b:v 0 -crf 38 -row-mt 1 assets/images/anuncios/billboard.webm`
   - no mobile, os mesmos comandos com `billboard-mobile.mp4` e `billboard-mobile.webm`.
   O `portal.js` toca o vídeo por cima da imagem (até 3 vezes, com pausa de 4 s) e respeita
   `prefers-reduced-motion`. Sem os vídeos, fica só a imagem.
5. Rode `python build/gerar.py`.
