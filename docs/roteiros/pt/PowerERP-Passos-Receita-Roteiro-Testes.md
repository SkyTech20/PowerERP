# PowerERP — Registros dos passos da receita no chão de fábrica: roteiro de testes

Roteiro para testar o card **Recipe steps** da tela **Production > Production orders** (passo 6 do plano SCOR / ISO, M4: ISO 9001 8.5.1, HACCP / ISO 22000 8.5.4 monitoramento dos pontos críticos de controle, registros de controle preventivo SFCR). O operador segue os passos da receita da ordem e registra cada um: o valor medido ou ajustado, ou "feito". Um valor fora dos limites é um desvio e pede a ação corretiva; num passo crítico o desvio **bloqueia** a ordem ou **segura o lote** em **Quality > Lot status**. Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**. Os valores esperados são os do cenário **Pastry shop**.

**Antes de começar:** entre como administrador, vá em **Administration > System settings**, escolha o cenário **Pastry shop** e restaure os dados de demo.

---

## 1. A massa: um passo dentro dos limites

**Production > Production orders**, **New**

| Passo | Esperado |
|---|---|
| DOUGH, 10 KG, **Save** | Ordem 1 em rascunho: **não** aparece o card *Recipe steps* (só depois de liberar). |
| **Release** | Aparece o card **Recipe steps** acima do *Shop floor*: selo "Required steps: 0 of 1 done", os passos agrupados por operação (10 — ..., 20 — ..., 30 — ...), cada um com número, ícone, título e o selo *To do*. |
| No passo *Add warm water*: campo *EAU (L)* com "min 3.4 · max 3.8" embaixo | Os limites da receita. |
| Digitar 4 e sair do campo | Logo embaixo: selo vermelho "Above the maximum → warning" e "Write the corrective action." O campo *Corrective action* fica vermelho. Nada foi gravado. |
| Trocar para 3,6 e sair do campo | Selo verde "✓ Within its limits". |
| **Record** | "Step recorded." O passo fica *Done* (fundo verde) com a linha "✓ 3,6 L · admin · data e hora". O selo de cima: "Required steps: 1 of 1 done". Aparece "Record again" (fechado). |
| Nos passos sem valor (*Weigh the flour*, *Mix for 15 minutes*, *Rest the dough*) **Mark as done** | Cada um fica *Done* com "✓ Done · admin · data". |
| No *Shop floor*: **Issue**, *Quantity made* 9,8, **Report** | Ordem em andamento, lote MO1. |

## 2. O pastel: passo crítico que bloqueia

**New**: PASTEL-HAM-CHEESE, 40 UN, **Save**, **Release**, **Issue**

| Passo | Esperado |
|---|---|
| Card *Recipe steps* | "Required steps: 0 of 2 done". O passo *Pastels well sealed* tem a borda vermelha e os selos *Critical · blocks the next step* e *Required*. |
| *Pastels well sealed*: *Value* **No**, **Record** sem ação corretiva | Erro no próprio passo e no aviso: "The value is out of its limits: write the corrective action (Not confirmed)". O que foi escolhido continua no campo. |
| *Corrective action* "3 pastéis abertos: fechados à mão", **Record** | O passo fica *Deviation* (fundo rosa) com "⛔ Out of its limits: record it again within its limits to go on". A linha do registro: "⚠ No · admin · data" e embaixo "Not confirmed → blocks the next step · Corrective action: 3 pastéis abertos...". No alto do card: selo "1 deviation(s)" e o quadro vermelho "Reporting and completing are blocked until these critical steps are recorded again within their limits: 10/30 Pastels well sealed". |
| *Shop floor*: acima do botão **Report** | O mesmo aviso vermelho de bloqueio. |
| **Report** (40) | Recusado: "A critical step is out of its limits: record it again within its limits first (10/30 Pastels well sealed)". Nada entra no estoque. |
| *Pastels well sealed*: *Value* **Yes**, **Record** | O passo volta a *Done*; os dois registros ficam na lista (o mais novo em cima). O bloqueio some. |
| **Report** (40) | Agora aceito: lote MO2. |
| Card *History* | Uma linha *Deviation* com "10/30 Pastels well sealed: no (not_confirmed) — 3 pastéis abertos...". |

## 3. A temperatura do óleo: desvio que só avisa

| Passo | Esperado |
|---|---|
| *Oil temperature* (TEMP_HUILE, 175 a 185 °C): 190, **Record** sem ação | Recusado: pede a ação corretiva. |
| *Corrective action* "Fogo baixado, 180 °C após 2 min", **Record** | *Deviation*, mas sem bloqueio (não é crítico: "Above the maximum → warning"). O **Report** e o **Complete** continuam possíveis. Selo "2 deviation(s)". |
| 180, **Record** | *Done*; o desvio continua listado no passo e contado no selo. |

## 4. A carne moída: passo crítico que segura o lote

**New**: GROUND-BEEF, 5 KG, **Save**, **Release**, **Issue**

| Passo | Esperado |
|---|---|
| Passo *Core temperature* (TEMP_COEUR, min 71 °C, *Each lot*) | Selos *Critical · the lot is held* e *Required*; "Each lot" embaixo do título; campos *TEMP_COEUR (°C)*, *Lot* (vazio: o lote ainda não existe) e *Corrective action*. |
| 65, *Corrective action* "Cozido mais 5 minutos, medir de novo", **Record** | *Deviation* "Below the minimum → the lot is held". Ainda não há lote: nada é segurado agora. |
| *Shop floor*: **Report** (5) | Aceito (segurar o lote não bloqueia): lote MO3. |
| **Quality > Lot status** | Quadro *On hold* 1: GROUND-BEEF MO3 *On hold*, motivo "Order 3, step 20/10 Core temperature: 65 °C", admin e a data. |
| Voltar à ordem 3, *Core temperature*: **Record again**, 75, *Lot* MO3, **Record** | *Done* (1/1). O lote **continua** *On hold*: quem libera é a qualidade (**Change status** em *Lot status*, com o motivo). |
| Em *Lot status*, MO3 **Change status** → *Released*, motivo "Recozido e medido 75 °C" | O lote volta a *Released*. Um novo **Report** do mesmo lote MO3 não o segura de novo. |

## 5. Segunda assinatura e perfil exigido (cenário Manufacturing, opcional)

O demo da pastelaria não tem passo com segunda assinatura. Para testar: **Administration > System settings**, cenário **Manufacturing**, restaurar; **Administration > Users**, **New**: usuário *op1*, perfil USER, senha *Secret-123*.

| Passo | Esperado |
|---|---|
| **Production > Production orders**, **New**: PAIN-BL-675, 400, **Save**, **Release** | Card *Recipe steps*. O passo *Mixer clean (cleaning checked)* tem o selo *✍️ 2nd signature* e os campos *Second signer (user)* e *Their password*. O passo *Dough too cold: correction* aparece apagado, *Does not apply* ("Only if TEMP_PATE < 24"). |
| *Mixer clean*: Yes, **Record** sem segundo usuário | "Required" no usuário. |
| *Second signer* admin (o próprio usuário logado), senha certa | Recusado: "The second signature must be another user". |
| *Second signer* op1, senha errada | "Wrong user or password for the second signature". Em **Administration > Audit log**: evento *Second signature refused* de op1. |
| *Second signer* op1, senha *Secret-123*, **Record** | *Done*; a linha mostra "admin + op1". |
| *Dough temperature* 22, ação corretiva "Água morna", **Record** | *Deviation* (warning). O passo *Dough too cold: correction* passa a *To do*. |
| Ordem de SUPP-ALU-01: passo *Release by quality control* (selo "Signed by: quality") com op1 | "This step must be signed by a user of the role (quality)". Com um administrador: aceito. |

## 6. Permissões

| Passo | Esperado |
|---|---|
| Com um perfil que tem *Production orders* só em **View** | O card *Recipe steps* aparece com os registros, sem campos nem botões. |
| Ordem *Completed* ou *Closed* | O card fica só de leitura. |
