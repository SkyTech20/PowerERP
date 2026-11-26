# PowerERP — Registros dos passos da receita no chão de fábrica: roteiro de testes

Roteiro para testar o card **Recipe steps** da tela **Production > Production orders** (passo 6 do plano SCOR / ISO, M4: ISO 9001 8.5.1, HACCP / ISO 22000 8.5.4 monitoramento dos pontos críticos de controle, registros de controle preventivo SFCR). O operador segue os passos da receita da ordem e registra cada um: o valor medido ou ajustado, ou "feito". Um valor fora dos limites é um desvio e pede a ação corretiva; num passo crítico o desvio **bloqueia** a ordem ou **segura o lote** em **Quality > Lot status**. Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**. Os valores esperados são os do cenário **Maple products**.

**Antes de começar:** entre como administrador, vá em **Administration > System settings**, escolha o cenário **Maple products** e restaure os dados de demo. O demo já traz as ordens 1 a 13: as novas começam na 14. A ordem 9 (bonbons cozidos a 118,5 °C) é um exemplo pronto de desvio que segurou o lote.

---

## 1. O sirop padronizado: um passo dentro dos limites

**Production > Production orders**, **New**

| Passo | Esperado |
|---|---|
| SYRUP-STD, 100 KG, **Save** | Ordem 14 em rascunho: **não** aparece o card *Recipe steps* (só depois de liberar). |
| **Release** | Aparece o card **Recipe steps** acima do *Shop floor*: selo "Required steps: 0 of 2 done", os passos agrupados por operação (10 — MPL-BLEND, 20 — MPL-FILTER), cada um com número, ícone, título e o selo *To do*. |
| No passo *Syrup Brix (66 to 68.9)*: campo *BRIX (°Bx)* com "min 66 · max 68.9" embaixo | Os limites da receita. Selos *Critical · blocks the next step* e *Required*. |
| Digitar 70 e sair do campo | Logo embaixo: selo vermelho "Above the maximum → blocks the next step" e "Write the corrective action." O campo *Corrective action* fica vermelho. Nada foi gravado. |
| Trocar para 67,2 e sair do campo | Selo verde "✓ Within its limits". |
| **Record** | "Step recorded." O passo fica *Done* (fundo verde) com a linha "✓ 67,2 °Bx · admin · data e hora". O selo de cima: "Required steps: 1 of 2 done". Aparece "Record again" (fechado). |
| Nos passos sem valor (*Empty the barrels (scan the lot)*, *Filter for 60 minutes*) **Mark as done** | Cada um fica *Done* com "✓ Done · admin · data". |

## 2. O gosto dos barris: passo crítico que bloqueia

Na mesma ordem 14:

| Passo | Esperado |
|---|---|
| *Taste and smell of the barrels are right* | Borda vermelha, selos *Critical · blocks the next step* e *Required*. |
| *Value* **No**, **Record** sem ação corretiva | Erro no próprio passo e no aviso: "The value is out of its limits: write the corrective action (Not confirmed)". O que foi escolhido continua no campo. |
| *Corrective action* "Baril 900106-2 : goût de bourgeon", **Record** | O passo fica *Deviation* (fundo rosa) com "⛔ Out of its limits: record it again within its limits to go on". No alto do card: selo "1 deviation(s)" e o quadro vermelho "Reporting and completing are blocked until these critical steps are recorded again within their limits: 10/20 Taste and smell of the barrels are right". |
| *Shop floor*: **Issue**, depois *Quantity made* 100, **Report** | O **Issue** passa; o **Report** é recusado: "A critical step is out of its limits: record it again within its limits first (10/20 Taste and smell of the barrels are right)". Nada entra no estoque. |
| *Taste and smell...*: *Value* **Yes**, **Record** | O passo volta a *Done*; os dois registros ficam na lista (o mais novo em cima). O bloqueio some. |
| **Report** (100, *Location* TANK-01) | Aceito: lote MO14. |
| Card *History* | Uma linha *Deviation* com "10/20 Taste and smell of the barrels are right: no (not_confirmed) — Baril 900106-2 : goût de bourgeon". |

## 3. O beurre d'érable: passo crítico que segura o lote

**New**: MAPLE-BUTTER-200, 100 UN, **Save**, **Release**, **Issue** (ordem 15)

| Passo | Esperado |
|---|---|
| Passos *Cook to 112 °C* (TEMP_CUISSON, 111 a 113) e *Cool below 10 °C before whipping* (TEMP_REFROID, máximo 10) | Selos *Critical · the lot is held* e *Required*; "Each lot" embaixo do título; campos do valor, *Lot* (vazio: o lote ainda não existe) e *Corrective action*. |
| *Cook to 112 °C*: 112,1, **Record** | *Done*. |
| *Cool below 10 °C...*: 14, *Corrective action* "Bac de refroidissement trop plein ; refroidi de nouveau", **Record** | *Deviation* "Above the maximum → the lot is held". Ainda não há lote: nada é segurado agora, e não há bloqueio. |
| *Shop floor*: **Report** (100) | Aceito (segurar o lote não bloqueia): lote MO15. |
| **Quality > Lot status** | Quadro *On hold* 2: MAPLE-BUTTER-200 MO15 *On hold*, motivo "Order 15, step 20/10 Cool below 10 °C before whipping: 14 °C", admin e a data; e o MO9 dos bonbons do demo. |
| Voltar à ordem 15, *Cool below 10 °C...*: **Record again**, 8, *Lot* MO15, **Record** | *Done*. O lote **continua** *On hold*: quem libera é a qualidade (**Change status** em *Lot status*, com o motivo). |
| Em *Lot status*, MO15 **Change status** → *Released*, motivo "Refroidi à 8 °C, texture vérifiée" | O lote volta a *Released* e pode ser vendido. |

## 4. Desvio que só avisa, segunda assinatura e perfil exigido (cenário Manufacturing, opcional)

No demo de bordo todos os passos com valor são críticos, e nenhum pede segunda assinatura. Para testar: **Administration > System settings**, cenário **Manufacturing**, restaurar; **Administration > Users**, **New**: usuário *op1*, perfil USER, senha *Secret-123*.

| Passo | Esperado |
|---|---|
| **Production > Production orders**, **New**: PAIN-BL-675, 400, **Save**, **Release** | Card *Recipe steps*. O passo *Mixer clean (cleaning checked)* tem o selo *✍️ 2nd signature* e os campos *Second signer (user)* e *Their password*. O passo *Dough too cold: correction* aparece apagado, *Does not apply* ("Only if TEMP_PATE < 24"). |
| *Mixer clean*: Yes, **Record** sem segundo usuário | "Required" no usuário. |
| *Second signer* admin (o próprio usuário logado), senha certa | Recusado: "The second signature must be another user". |
| *Second signer* op1, senha errada | "Wrong user or password for the second signature". Em **Administration > Audit log**: evento *Second signature refused* de op1. |
| *Second signer* op1, senha *Secret-123*, **Record** | *Done*; a linha mostra "admin + op1". |
| *Dough temperature* 22, ação corretiva "Água morna", **Record** | *Deviation* (warning). O passo *Dough too cold: correction* passa a *To do*. |
| Ordem de SUPP-ALU-01: passo *Release by quality control* (selo "Signed by: quality") com op1 | "This step must be signed by a user of the role (quality)". Com um administrador: aceito. |

## 5. Permissões

| Passo | Esperado |
|---|---|
| Com um perfil que tem *Production orders* só em **View** | O card *Recipe steps* aparece com os registros, sem campos nem botões. |
| Ordem *Completed* ou *Closed* | O card fica só de leitura. |
