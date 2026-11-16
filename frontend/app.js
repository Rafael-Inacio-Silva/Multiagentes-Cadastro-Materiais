"use strict";

const $ = (id) => document.getElementById(id);
const PARALELOS = new Set(["numero", "nome", "material", "tipo", "geometria"]);
const DESENHO_EXEMPLO = "exemplo/eixo-transmissao.png";

let aoVivo = false;
let rodando = false;
let cadastroAtual = null;
let relogio = null;

/* navegação ----------------------------------------------------------- */
document.querySelectorAll(".item[data-tela]").forEach((botao) => {
  botao.addEventListener("click", () => {
    document.querySelectorAll(".item[data-tela]").forEach((b) => b.classList.toggle("ativo", b === botao));
    $("tela-analisar").hidden = botao.dataset.tela !== "analisar";
    $("tela-agentes").hidden = botao.dataset.tela !== "agentes";
  });
});

/* estado do servidor -------------------------------------------------- */
async function carregarEstado() {
  try {
    const estado = await (await fetch("api/estado")).json();
    aoVivo = estado.ao_vivo;
    $("modelo").textContent = estado.modelo;
    pilula($("modo"), aoVivo ? "verde" : "amarelo", aoVivo ? "ao vivo" : "execução gravada");
    if (!aoVivo) {
      $("rot-arquivo").classList.add("desligado");
      $("dica").textContent = "Sem OPENAI_API_KEY: o exemplo repete uma execução real gravada.";
    }
  } catch {
    pilula($("modo"), "vermelho", "servidor fora do ar");
  }
}

function pilula(el, cor, texto, pulsa = false) {
  el.innerHTML = `<span class="ponto ${cor}${pulsa ? " pulsa" : ""}"></span>${texto}`;
}

/* execução ------------------------------------------------------------ */
$("btn-exemplo").addEventListener("click", () => {
  mostrarDesenho(DESENHO_EXEMPLO, "eixo-transmissao.png · desenho sintético");
  executar(fetch(aoVivo ? "api/exemplo" : "api/exemplo?gravado=1"));
});

$("arquivo").addEventListener("change", (e) => {
  const arquivo = e.target.files[0];
  e.target.value = "";
  if (!arquivo) return;
  mostrarDesenho(URL.createObjectURL(arquivo), arquivo.name);
  const dados = new FormData();
  dados.append("arquivo", arquivo);
  executar(fetch("api/analisar", { method: "POST", body: dados }));
});

function mostrarDesenho(src, nome) {
  $("folha").innerHTML = `<img alt="Desenho técnico enviado" src="${src}">`;
  $("nome-arquivo").textContent = nome;
}

async function executar(pedido) {
  if (rodando) return;
  rodando = true;
  travar(true);
  limpar();
  pilula($("situacao"), "amarelo", "analisando", true);
  const inicio = performance.now();
  relogio = setInterval(() => {
    $("tempo").textContent = `${((performance.now() - inicio) / 1000).toFixed(1)} s`;
  }, 100);

  try {
    const resposta = await pedido;
    if (!resposta.ok) {
      const corpo = await resposta.json().catch(() => ({}));
      throw new Error(corpo.detail || `erro ${resposta.status}`);
    }
    await lerEventos(resposta.body, tratar);
  } catch (erro) {
    mostrarFora("Não foi possível analisar", erro.message);
    pilula($("situacao"), "vermelho", "erro");
  } finally {
    clearInterval(relogio);
    rodando = false;
    travar(false);
  }
}

async function lerEventos(corpo, aoEvento) {
  const leitor = corpo.getReader();
  const decodificador = new TextDecoder();
  let pendente = "";
  for (;;) {
    const { value, done } = await leitor.read();
    if (done) break;
    pendente += decodificador.decode(value, { stream: true });
    let fim;
    while ((fim = pendente.indexOf("\n")) >= 0) {
      const linha = pendente.slice(0, fim).trim();
      pendente = pendente.slice(fim + 1);
      if (linha) aoEvento(JSON.parse(linha));
    }
  }
}

function tratar(evento) {
  switch (evento.evento) {
    case "inicio":
      desenharAgentes(evento.agentes);
      $("modelo").textContent = evento.modelo;
      $("sub").textContent = evento.gravado
        ? `execução real gravada em ${evento.gravado_em} · repetida no mesmo ritmo`
        : "execução ao vivo · cada cartão acende quando o agente responde";
      break;
    case "agente":
      atualizarAgente(evento);
      break;
    case "fora_do_escopo":
      mostrarFora("Fora do escopo do MVP", evento.motivo);
      pilula($("situacao"), "vermelho", "fora do escopo");
      break;
    case "cadastro":
      mostrarCadastro(evento.cadastro);
      break;
    case "fim":
      clearInterval(relogio);
      $("tempo").textContent = `${(evento.ms / 1000).toFixed(1)} s no total`;
      if (cadastroAtual) {
        const pendencias = cadastroAtual.pendencias.length;
        pilula($("situacao"), pendencias ? "amarelo" : "verde",
          pendencias ? `concluído · ${pendencias} para revisar` : "concluído");
      }
      break;
  }
}

/* agentes ------------------------------------------------------------- */
function desenharAgentes(agentes) {
  const lista = $("agentes");
  lista.innerHTML = "";
  let separou = false;
  for (const agente of agentes) {
    if (PARALELOS.has(agente.id) && !separou) {
      lista.insertAdjacentHTML("beforeend", `<li class="separador">em paralelo</li>`);
      separou = true;
    }
    const selo = agente.ia ? `<span class="selo">IA</span>` : `<span class="selo codigo">CÓDIGO</span>`;
    lista.insertAdjacentHTML("beforeend", `
      <li class="agente${PARALELOS.has(agente.id) ? " paralelo" : ""}" id="ag-${agente.id}">
        <span class="ponto cinza"></span>
        <span class="nome">${agente.nome} ${selo}</span>
        <span class="ms"></span>
        <span class="papel">${agente.papel}</span>
        <span class="resumo"></span>
      </li>`);
  }
}

function atualizarAgente(evento) {
  const item = $(`ag-${evento.id}`);
  if (!item) return;
  const cor = { rodando: "amarelo pulsa", ok: "verde", erro: "vermelho" }[evento.estado];
  item.querySelector(".ponto").className = `ponto ${cor}`;
  item.classList.toggle("erro", evento.estado === "erro");
  item.classList.toggle("feito", evento.estado === "ok" || evento.estado === "erro");
  if (evento.ms !== undefined) item.querySelector(".ms").textContent = `${(evento.ms / 1000).toFixed(1)} s`;
  if (evento.estado === "ok") item.querySelector(".resumo").textContent = evento.resumo || "";
  if (evento.estado === "erro") item.querySelector(".resumo").textContent = "falhou: campo vai para revisão";
}

/* cadastro ------------------------------------------------------------ */
function mostrarCadastro(c) {
  cadastroAtual = c;
  const peso = c.peso_kg != null ? `${formatar(c.peso_kg)} kg` : "—";
  const notaPeso = c.peso
    ? c.peso.origem === "calculado pela geometria"
      ? `${formatar(c.peso.volume_cm3)} cm³ × ${formatar(c.peso.densidade_kg_m3)} kg/m³`
      : c.peso.origem
    : "";
  const blocos = [
    ["Nº do desenho", c.numero_desenho, c.revisao != null ? `revisão ${c.revisao}` : ""],
    ["Denominação", c.denominacao, ""],
    ["Material", c.material, ""],
    ["Tipo de item", c.tipo_item_rotulo, ""],
    ["Dimensão principal", c.dimensao_principal, ""],
    ["Peso", c.peso_kg != null ? peso : null, notaPeso],
  ];
  $("numeros").innerHTML = blocos.map(([rotulo, valor, nota]) => `
    <div class="numero${valor ? " destaque" : ""}">
      <div class="rot">${rotulo}</div>
      <div class="val">${valor ? escapar(valor) : '<span class="fraco">não encontrado</span>'}</div>
      ${nota ? `<div class="nota">${escapar(nota)}</div>` : ""}
    </div>`).join("");
  $("texto-breve").textContent = c.texto_breve || "—";
  $("tb-tamanho").textContent = c.texto_breve ? `· ${c.texto_breve.length}/40` : "";
  $("pendencias").innerHTML = c.pendencias.length
    ? `<div class="aviso"><b>Para o cadastrista revisar</b><ul>${c.pendencias.map((p) => `<li>${escapar(p)}</li>`).join("")}</ul></div>`
    : "";
  $("cartao-cadastro").hidden = false;
}

$("btn-copiar").addEventListener("click", async () => {
  if (!cadastroAtual?.texto_breve) return;
  try {
    await navigator.clipboard.writeText(cadastroAtual.texto_breve);
    $("btn-copiar").textContent = "Copiado";
    setTimeout(() => ($("btn-copiar").textContent = "Copiar texto breve"), 1500);
  } catch { /* área de transferência bloqueada: nada a fazer */ }
});

$("btn-json").addEventListener("click", () => {
  if (!cadastroAtual) return;
  const blob = new Blob([JSON.stringify(cadastroAtual, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `cadastro-${cadastroAtual.numero_desenho || "material"}.json`;
  link.click();
  URL.revokeObjectURL(link.href);
});

/* utilidades ---------------------------------------------------------- */
function limpar() {
  cadastroAtual = null;
  $("cartao-cadastro").hidden = true;
  $("fora").hidden = true;
  $("agentes").innerHTML = "";
  $("tempo").textContent = "";
}

function travar(sim) {
  $("btn-exemplo").disabled = sim;
  $("rot-arquivo").classList.toggle("desligado", sim || !aoVivo);
}

function mostrarFora(titulo, texto) {
  $("fora").innerHTML = `<b>${escapar(titulo)}</b>${escapar(texto)}`;
  $("fora").hidden = false;
}

function formatar(n) {
  return Number(n).toLocaleString("pt-BR", { maximumFractionDigits: 2 });
}

function escapar(texto) {
  return String(texto).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

carregarEstado();
