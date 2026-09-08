/**
 * BorisFlat.jsx — ilustração flat/cartoon do Boris, meio-corpo (Fase 23,
 * ILUS-01). Usada SÓ no modal de introdução (`BorisIntro.jsx`), no lugar do
 * `<Boris size={110}/>` (PNG 490×655, sombreado/textura de pena) que destoava
 * do resto da marca — flat/vetorial em tudo mais (`LogoMark`, ícone do app).
 *
 * `PetFab` continua com o PNG semi-realista de `Boris.jsx` (asset em
 * `web/src/assets/`), sem mudança — decisão de escopo do kickoff do
 * milestone v1.5, registrada no ROADMAP: "a troca de arte se limita ao
 * modal de introdução".
 *
 * Os hex abaixo são LITERAIS (não `BRAND.amber`/tokens de `App.jsx`) porque
 * importar qualquer coisa de `App.jsx` a partir de `pet/` recriaria o import
 * circular que `BorisIntro.jsx` já documenta ter contornado (App.jsx importa
 * `Boris`/`BorisChat`/`BorisIntro` de `./pet/*.jsx`; a direção inversa
 * quebraria o build). Fonte de verdade dos valores: `LogoMark`
 * (`web/src/App.jsx:201-231`) — qualquer mudança de marca nestas cores tem
 * que ser feita NOS DOIS lugares.
 *
 * Regra de marca travada (comentário de `LogoMark`, `App.jsx:202-206`,
 * fechada na v2 do Brand Book): óculos e bico são âmbar (`#f2a93b`) em
 * QUALQUER tema (claro/escuro) e QUALQUER modo (Estudo/Operador) — nunca
 * seguem o token de acento do tema. Corpo/rosto são sempre `#2a3a6b`. Por
 * isso esta ilustração não é temável: nenhum token de tema aparece aqui.
 *
 * O rosto (tufos, círculo do rosto, óculos, ponte, olhos, bico) é copiado
 * VERBATIM da geometria de `LogoMark` — mesmos `cx`/`cy`/`r`/`d`/
 * `strokeWidth`, só deslocado para o `viewBox` maior (0 0 64 92) que abre
 * espaço para o corpo abaixo. O corpo é a única parte nova, desenhada ANTES
 * do rosto na ordem do documento para o rosto ficar por cima.
 */
export default function BorisFlat({ size = 110 }) {
  const width = size;
  const height = Math.round(size * 92 / 64);
  return (
    <svg width={width} height={height} viewBox="0 0 64 92" fill="none" aria-hidden role="img" style={{ display: "block", flex: "none" }}>
      {/* corpo — a única parte inventada; nasce atrás do rosto, desce até o pé */}
      <path d="M32 30 C48 30 54 44 54 60 C54 78 44 88 32 88 C20 88 10 78 10 60 C10 44 16 30 32 30 Z" fill="#2a3a6b" />
      {/* gravata — mesmo âmbar da marca, elemento discricionário do PNG atual */}
      <path d="M32 58 L37 66 L32 84 L27 66 Z" fill="#f2a93b" />
      {/* tufos de orelha — copiados verbatim de LogoMark */}
      <path d="M14 16 L22 27 L10 27 Z" fill="#2a3a6b" />
      <path d="M50 16 L42 27 L54 27 Z" fill="#2a3a6b" />
      {/* rosto — copiado verbatim de LogoMark */}
      <circle cx="32" cy="34" r="26" fill="#2a3a6b" />
      {/* óculos redondos — sempre âmbar, nunca o acento do modo */}
      <circle cx="22" cy="32" r="10" fill="none" stroke="#f2a93b" strokeWidth="3.2" />
      <circle cx="42" cy="32" r="10" fill="none" stroke="#f2a93b" strokeWidth="3.2" />
      <path d="M30 32 Q32 29 34 32" fill="none" stroke="#f2a93b" strokeWidth="3.2" />
      <circle cx="22" cy="32" r="4" fill="#eef1f8" />
      <circle cx="42" cy="32" r="4" fill="#eef1f8" />
      {/* bico — sempre âmbar */}
      <path d="M32 42 L27.5 49 L36.5 49 Z" fill="#f2a93b" />
    </svg>
  );
}
