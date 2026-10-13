# Briefing de imagens — Arena Diária

Uma imagem por matéria. Ela vira a foto de capa da página, a miniatura na home e a prévia no
Facebook, Instagram e WhatsApp (og:image).

## Como entregar

- Salve cada imagem nesta pasta (`build/fotos/`) com o **nome exato** da tabela, por exemplo
  `noticia-copa-do-brasil.jpg`. Pode ser JPG, PNG ou WebP.
- Depois rode `python build/gerar.py`. O gerador recorta, redimensiona, comprime e publica em
  `assets/images/fotos/` (JPG com menos de 300 KB e WebP). Sem imagem, a matéria segue com a arte atual.

## Regras para todas as imagens (SEO e Meta)

- **Formato horizontal 1,91:1.** Gere em **1200 x 630 px** ou maior na mesma proporção (por exemplo
  1600 x 840 ou 1920 x 1008). Se vier 16:9, o gerador corta um pouco em cima e embaixo.
- **Assunto no centro.** As bordas são cortadas nas miniaturas; deixe margem de uns 10% em volta.
- **Fotografia editorial realista**, luz natural, cara de foto de jornal. Nada de ilustração 3D,
  cartoon ou estética de anúncio.
- **Sem texto, letras, números, placares ou marcas d'água na imagem.** O título já vem na página.
- **Sem marcas reais:** nenhum escudo de clube, logotipo de patrocinador, marca de material
  esportivo, logo da CBF, da Conmebol, de banco ou de TV. Camisas lisas ou genéricas.
- **Sem pessoas reconhecíveis:** nada de jogadores, técnicos ou famosos reais. Pessoas de costas,
  desfocadas ou em plano aberto.
- **Sem nada de apostas:** nada de cassino, fichas, odds, cartas, roleta ou telas de aposta.
- **Sem conteúdo chocante ou sensacionalista.**
- A página mostra a legenda "Imagem ilustrativa gerada com inteligência artificial".

## Imagens

| Arquivo | Matéria | Descrição | Prompt (inglês) |
|---|---|---|---|
| `noticia-brasileirao-rodada.jpg` | Como funciona o Brasileirão | Estádio lotado à noite, gramado iluminado visto da arquibancada | Editorial sports photograph, wide shot of a packed Brazilian football stadium at night seen from the upper stands, bright floodlights on a green pitch, crowd as soft silhouettes, no logos, no text, no readable signage, natural colors, 35mm lens |
| `noticia-selecao-brasileira.jpg` | Seleção Brasileira | Bola no gramado e arquibancada de amarelo e verde ao fundo | Editorial photograph, close-up of a plain white football resting on the grass at pitch level, blurred stadium stands in the background filled with fans wearing plain yellow and green shirts, shallow depth of field, golden hour light, no crests, no logos, no text |
| `noticia-patrocinios-futebol.jpg` | Patrocínio no futebol | Camisa lisa pendurada no vestiário | Editorial photograph of a plain football jersey without any logo hanging on a hook in a clean locker room, empty chest area, wooden benches, soft side light, realistic, no text, no brands |
| `noticia-copa-do-brasil.jpg` | Como funciona a Copa do Brasil | Taça dourada à beira do gramado | Editorial photograph of a generic golden football trophy on a pedestal at the edge of the pitch, blurred stadium lights behind, evening, realistic, no engraving, no logos, no text |
| `noticia-libertadores.jpg` | Como funciona a Libertadores | Disputa de bola em estádio sul-americano à noite | Editorial sports photograph, two football players in plain unbranded kits (one white, one dark blue) contesting the ball in a crowded South American stadium at night, motion, faces turned away or blurred, smoke and floodlights, no logos, no text |
| `noticia-direitos-de-transmissao.jpg` | Direitos de transmissão | Câmera de TV na lateral do campo | Editorial photograph of a professional broadcast TV camera on the sideline of a football pitch during a match, camera operator seen from behind, blurred players in the background, no brand names, no text |
| `noticia-saf-sociedade-anonima-futebol.jpg` | O que é a SAF | Mesa de reunião com contrato e bola | Editorial photograph of a boardroom table with a printed contract, a pen and a football, large window showing an out-of-focus stadium, soft daylight, professional, no readable text, no logos |
| `noticia-ingressos-direitos-torcedor.jpg` | Direitos do torcedor nos ingressos | Ingresso no celular na catraca | Editorial photograph of a fan holding a smartphone with a generic QR-code ticket near a stadium turnstile, hand and phone in focus, crowd blurred, no readable text, no logos |
| `noticia-pix-golpes-med.jpg` | Pix: golpes e devolução (MED) | Celular com confirmação de pagamento | Editorial photograph of a hand holding a smartphone showing a generic green payment confirmation screen with a check mark, kitchen table background, soft daylight, no readable text, no bank logos |

## Imagem padrão do site (opcional)

`og-arena-diaria.jpg` é a prévia da home e das páginas institucionais. Hoje é uma arte com o nome
do portal. Se quiser trocar, gere 1200 x 630 seguindo as mesmas regras e me avise: essa imagem é
a única que pode ter o nome "Arena Diária" escrito.
