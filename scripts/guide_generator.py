#!/usr/bin/env python3
"""
Guide Generator — Seleziona e prepara la guida "Impara Oggi" del giorno.
Ruota tra i temi in config.json in base alla data.
Output: data/daily_guide.json
"""

import json
import hashlib
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


# ─── Pre-built guide content ────────────────────────
# Each guide has Italian content ready to use.
# We can generate more with AI later.

GUIDE_CONTENT = {
    "Cos'è un LLM e come funziona": {
        "content_html": """
<p>Un <strong>LLM</strong> (Large Language Model) è un'intelligenza artificiale addestrata su enormi quantità di testo per imparare a prevedere la parola successiva in una frase.</p>
<p><strong>Il concetto chiave:</strong> Quando scrivi "Il gatto è salito sul..." l'LLM calcola la probabilità di ogni parola possibile. "Tavolo" ha alta probabilità, "giraffa" ha bassa probabilità. Non "pensa" — calcola statistiche.</p>
<ul>
  <li><strong>Training:</strong> L'LLM legge miliardi di pagine web, libri, articoli — e impara schemi linguistici</li>
  <li><strong>Parametri:</strong> GPT-4 ha ~1.8 trilioni di parametri — numeri che rappresentano la "conoscenza"</li>
  <li><strong>Contesto:</strong> L'LLM "ricorda" solo le ultime migliaia di token (parole) della conversazione</li>
  <li><strong>Token:</strong> L'unità base — "intelligenza" potrebbe essere 2-3 token, non una parola intera</li>
</ul>
<p><strong>Perché è importante:</strong> Capire che l'LLM è un predittore statistico, non un essere pensante, ti aiuta a usarlo meglio. Sapevi che non "sa" nulla — associa pattern.</p>
"""
    },
    "Prompt Engineering: le tecniche che funzionano": {
        "content_html": """
<p>Il <strong>prompt engineering</strong> è l'arte di scrivere istruzioni efficaci per un'AI. La stessa richiesta formulata in modo diverso può dare risultati completamente diversi.</p>
<p><strong>3 tecniche che funzionano davvero:</strong></p>
<ul>
  <li><strong>1. Sii specifico:</strong> Non "scrivi un articolo" ma "scrivi un articolo di 500 parole per un blog tech, tono informale, pubblico principiante, sul tema RAG"</li>
  <li><strong>2. Dai un ruolo:</strong> "Agisci come un senior developer con 10 anni di esperienza in Python" — il contesto cambia completamente la risposta</li>
  <li><strong>3. Esempi (few-shot):</strong> Mostra 2-3 esempi di cosa vuoi. L'LLM impara dal pattern meglio che dalle istruzioni</li>
</ul>
<p><strong>Chain-of-Thought:</strong> Aggiungi "Pensa passo dopo passo" per problemi complessi. L'LLM dividerà il ragionamento in fasi, riducendo gli errori.</p>
<p><strong>Il segreto:</strong> Tratta l'AI come un neo-assunto brillante ma letterale. Più contesto e chiarezza dai, meglio lavora.</p>
"""
    },
    "RAG: quando l'AI usa i tuoi documenti": {
        "content_html": """
<p><strong>RAG</strong> (Retrieval-Augmented Generation) è la tecnica che permette a un'AI di rispondere usando i TUOI documenti, non solo quello che ha imparato durante il training.</p>
<p><strong>Come funziona:</strong></p>
<ul>
  <li><strong>1. Indicizzazione:</strong> I tuoi documenti vengono divisi in pezzi e trasformati in vettori numerici (embeddings)</li>
  <li><strong>2. Ricerca:</strong> Quando fai una domanda, viene anch'essa trasformata in vettore e confrontata con i documenti</li>
  <li><strong>3. Recupero:</strong> I pezzi più simili alla tua domanda vengono selezionati</li>
  <li><strong>4. Generazione:</strong> L'LLM riceve i pezzi rilevanti + la tua domanda e genera una risposta basata su di essi</li>
</ul>
<p><strong>Perché è importante:</strong> Senza RAG, l'AI inventa risposte basandosi su pattern generici. Con RAG, risponde basandosi sui fatti contenuti nei tuoi documenti. È la differenza tra un consulente generico e uno che ha letto il tuo caso specifico.</p>
<p><strong>Tool:</strong> LangChain, LlamaIndex, e vector DB come Chroma, Pinecone, o Weaviate.</p>
"""
    },
    "Allucinazioni: perché l'AI inventa e come ridurle": {
        "content_html": """
<p>Le <strong>allucinazioni</strong> sono il problema più conosciuto degli LLM: l'AI genera informazioni false con totale sicurezza.</p>
<p><strong>Perché succede:</strong></p>
<ul>
  <li>L'LLM è un predittore statistico — non "sa" cosa è vero, sa solo cosa <em>sembra</em> vero linguisticamente</li>
  <li>Se la probabilità di "Il presidente dell'Italia è Mario Rossi" è alta nel training, l'LLM lo dirà — anche se falso</li>
  <li>L'LLM non ha un meccanismo interno per verificare i fatti</li>
</ul>
<p><strong>Come ridurle:</strong></p>
<ul>
  <li><strong>RAG:</strong> Dai all'AI documenti verificati da cui attingere</li>
  <li><strong>Temperature bassa:</strong> Un valore vicino a 0 rende l'AI più "cautiosa" e fattuale</li>
  <li><strong>Chiedi fonti:</strong> "Cita la fonte" spesso smaschera le invenzioni</li>
  <li><strong>Verifica incrociata:</strong> Mai prendere per oro colato le risposte su fatti concreti</li>
</ul>
<p><strong>Regola d'oro:</strong> L'AI è ottima per generare e organizzare idee. È pericolosa come fonte primaria di fatti.</p>
"""
    },
    "Token, contesto e finestra: come l'AI legge": {
        "content_html": """
<p>Per usare bene un'AI, devi capire tre concetti fondamentali: <strong>token</strong>, <strong>contesto</strong>, e <strong>finestra</strong>.</p>
<p><strong>Token:</strong> L'unità di testo che l'AI processa. Non sono parole esatte:</p>
<ul>
  <li>"gatto" = 1 token</li>
  <li>"intelligenza" = 2-3 token</li>
  <li>"Supercalifragilistiche" = 4-5 token</li>
  <li>In media: 1 token ≈ 0.75 parole inglesi, ~0.5 parole italiane</li>
</ul>
<p><strong>Contesto (context):</strong> Tutto ciò che l'AI "vede" — il tuo prompt + la sua risposta precedente + eventuali documenti. Più contesto = più memoria nella conversazione.</p>
<p><strong>Finestra (context window):</strong> Il limite massimo di token. Oltre questo limite, l'AI "dimentica" le prime parti:</p>
<ul>
  <li>GPT-4: 128K token (~100K parole)</li>
  <li>Claude 3.5: 200K token (~150K parole)</li>
  <li>Gemini 1.5: 1M token (~750K parole)</li>
</ul>
<p><strong>Perché conta:</strong> Se stai usando RAG o analizzando documenti lunghi, la finestra determina quanti documenti puoi dare all'AI. Un paper di 50 pagiene rientra in una finestra 128K, ma un intero libro no.</p>
"""
    },
    "Agenti AI: come fanno le cose da soli": {
        "content_html": """
<p>Un <strong>agente AI</strong> è un'AI che non solo risponde a domande, ma <em>fa cose</em> — legge file, esegue comandi, naviga il web, scrive codice.</p>
<p><strong>La differenza con un chatbot:</strong></p>
<ul>
  <li><strong>Chatbot:</strong> Tu chiedi → Lui risponde. Loop singolo.</li>
  <li><strong>Agente:</strong> Tu dai un obiettivo → Lui pianifica → Esegue → Osserva il risultato → Riprova se necessario. Loop continuo.</li>
</ul>
<p><strong>Come funzionano:</strong></p>
<ul>
  <li><strong>Obiettivo:</strong> "Risolvi questo bug nel codice" — l'agente ha un goal chiaro</li>
  <li><strong>Strumenti:</strong> L'agente può usare tool (filesystem, browser, API) tramite function calling o MCP</li>
  <li><strong>Loop ReAct:</strong> Reason → Act → Observe → Repeat</li>
  <li><strong>Memoria:</strong> Ricorda cosa ha fatto nei passi precedenti</li>
</ul>
<p><strong>Esempi reali:</strong> Claude Code, Cursor Composer, OpenClaw, Devin. Tutti agenti con diversi livelli di autonomia.</p>
"""
    },
    "MCP: il protocollo che connette l'AI agli strumenti": {
        "content_html": """
<p>Il <strong>Model Context Protocol (MCP)</strong> è uno standard aperto (creato da Anthropic) che permette a qualsiasi AI di connettersi a qualsiasi strumento esterno.</p>
<p><strong>Il problema prima di MCP:</strong> Ogni AI aveva le sue integrazioni. Claude non usava gli stessi tool di GPT. Ogni connessione era un progetto a sé.</p>
<p><strong>La soluzione:</strong></p>
<ul>
  <li><strong>Server MCP:</strong> Un piccolo programma che espone strumenti (es: leggi file, cerca nel web, query SQL)</li>
  <li><strong>Client MCP:</strong> L'AI (Claude, OpenClaw, Cursor) si connette al server e può usare quegli strumenti</li>
  <li><strong>Protocollo standard:</strong> Scritto una volta, funziona con qualsiasi client</li>
</ul>
<p><strong>Esempio pratico:</strong> Un server MCP per PostgreSQL permette a qualsiasi AI con client MCP di fare query SQL. Ne scrivi uno e funziona con Claude, Cursor, e OpenClaw.</p>
<p><strong>Trasporti:</strong> <code>stdio</code> (locale, process-to-process) e <code>HTTP/SSE</code> (remoto, per servizi cloud).</p>
<p><strong>È come USB per l'AI:</strong> uno standard universale che rende tutto compatibile.</p>
"""
    },
    "AI coding assistants: come usarli bene": {
        "content_html": """
<p>I <strong>coding assistant AI</strong> sono strumenti che ti aiutano a scrivere, leggere e debuggare codice. Ma usarli bene non è banale — la differenza tra un principiante e un pro sta tutto nel <em>come</em> gli poni il problema.</p>
<p><strong>I 3 livelli di coding assist:</strong></p>
<ul>
  <li><strong>Autocomplete:</strong> Ti suggerisce la prossima riga mentre scrivi. Veloce, locale, zero frizione. (GitHub Copilot, Cursor Tab)</li>
  <li><strong>Chat inline:</strong> Chiedi "così fa questo codice?" o "refactora questa funzione". Risposte contestuali sul tuo progetto. (Cursor Chat, VS Code Copilot Chat)</li>
  <li><strong>Agent mode:</strong> Dai un obiettivo e l'AI modifica più file, esegue test, fixa errori. Autonomo ma supervisionabile. (Claude Code, Cursor Composer, Kilo Code)</li>
</ul>
<p><strong>3 regole d'oro:</strong></p>
<ul>
  <li><strong>1. Dai contesto:</strong> Non dire "scrivi una funzione" — di "scrivi una funzione Python che prende una lista di dict con chiavi 'name' e 'score', filtra quelli con score > 50, e ritorna ordinati per score descrescente". Più contesto = meno allucinazioni.</li>
  <li><strong>2. Leggi prima di accettare:</strong> L'AI scrive codice che <em>sembra</em> giusto. Sempre. Non significa che lo sia. Leggi, capisci, poi accetta.</li>
  <li><strong>3. Itera, non perfeziona:</strong> Chiedi una prima bozza, poi migliora con prompt mirati. "Ora aggiungi gestione errori", "Ora rendilo type-safe". Meglio 3 iterazioni veloci che un prompt monstre.</li>
</ul>
<p><strong>Il segreto dei pro:</strong> Usano l'AI per il codice boilerplate (CRUD, test, config) e scrivono a mano la logica critica. È come avere un tirocinante velocissimo — perfetto per il lavoro ripetitivo, da supervisionare per le decisioni importanti.</p>
"""
    },
}


def main():
    print("📖 Guide Generator — Selecting today's guide\n")

    with open(SCRIPTS_DIR / "config.json") as f:
        config = json.load(f)

    topics = config.get("guide_topics", [])
    if not topics:
        print("❌ No guide topics in config.json")
        sys.exit(1)

    # Select topic based on day of year (rotates through all topics)
    day_of_year = datetime.now().timetuple().tm_yday
    topic_index = day_of_year % len(topics)
    topic = topics[topic_index]

    title = topic["title"]
    print(f"  📅 Day {day_of_year} → Topic #{topic_index + 1}/{len(topics)}")
    print(f"  📝 {title}")
    print(f"  🏷️  {topic.get('tag', '')} | {topic.get('level', '')}")

    # Get content
    content = GUIDE_CONTENT.get(title)
    if content:
        content_html = content["content_html"]
        print(f"  ✅ Pre-built content loaded")
    else:
        content_html = "<p>Questa guida sarà generata automaticamente dal sistema AI. Controlla domani!</p>"
        print(f"  ⚠️  No pre-built content — placeholder used")

    guide = {
        "title": title,
        "level": topic.get("level", "principiante"),
        "tag": topic.get("tag", ""),
        "content_html": content_html,
        "selected_at": datetime.now(timezone.utc).isoformat(),
        "day_of_year": day_of_year,
        "topic_index": topic_index,
    }

    # Save
    guide_path = DATA_DIR / "daily_guide.json"
    with open(guide_path, "w") as f:
        json.dump(guide, f, indent=2, ensure_ascii=False)

    print(f"\n  💾 Saved to: {guide_path}")


if __name__ == "__main__":
    main()
