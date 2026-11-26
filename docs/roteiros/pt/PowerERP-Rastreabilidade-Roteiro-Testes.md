# PowerERP — Lotes e rastreabilidade: roteiro de testes

Roteiro para testar a tela **Production > Lots and traceability** (passo 3 do plano SCOR / ISO): de um lote, ver de onde veio (fornecedor, lote do fornecedor, pedido de compra; para um lote fabricado, os lotes das matérias), para onde foi (ordens de produção, lotes feitos com ele, clientes), o que um recall precisa alcançar e exportar tudo para Excel. Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**. Os valores esperados são os do cenário **Maple products** logo depois de restaurar o demo.

**Antes de começar:** entre como administrador, vá em **Administration > System settings**, escolha o cenário **Maple products** e restaure os dados de demo. O demo já traz outubro e novembro de 2026 feitos (barris recebidos, ordens fechadas, faturas postadas), então não é preciso preparar nada.

---

## 1. A tela

**Production > Lots and traceability**

| Passo | Esperado |
|---|---|
| Abrir a tela | Listas *Product* e *Lot* e a mensagem "Pick a product and a lot to see its trace." A lista *Lot* fica desativada até escolher o produto. |
| Abrir a lista *Product* | Só produtos com controle de lote: BUTTER, CREAM-35, MAPLE-BUTTER-200, MAPLE-CANDY-12, MAPLE-FUDGE-250, MAPLE-SYRUP-540, SYRUP-BULK-AMB, SYRUP-STD... As embalagens (CAN-540, BOX-12, LABEL) não aparecem. |
| Escolher MAPLE-SYRUP-540 | Lista *Lot*: MO2 — 2028-10-01 · 0 e MO8 — 2028-11-02 · 236 (validade e quantidade em mão). |
| Escolher MO8 | A rastreabilidade aparece na hora. O endereço passa a ser `#/prod/traceability/MAPLE-SYRUP-540/MO8` (dá para guardar ou mandar). |
| **?** | Abre a ajuda da tela; cada campo tem seu **?**. |

## 2. De trás para frente: o lote de latas MO8

| O que ver | Esperado |
|---|---|
| Os 4 números do alto | *Lots reached* 1, *Customers* 3, *Stock lines* 1, *Open orders* 0. |
| Caixa amarela | "For a recall: 1 lot(s) reached, 3 customer(s) to call, 1 stock line(s) to put on hold and 0 open order(s) to check." |
| Card *Origin* | "Made 2026-11-03 · Order 8 *Closed* · 1000 UN". Abaixo, os dois lotes de sirop padronizado usados: SYRUP-STD **MO1** (245 KG, feito pela Order 1) e **MO7** (475 KG, Order 7). |
| Abrir MO1 dentro da origem | Os barris SYRUP-BULK-AMB 900102-1, 900102-2, 900102-3 (GAGNON, lotes do produtor B-0412, B-0418, B-0425) e 900104-3 (CANTONS, C-2101). Cada um mostra "Received ... · Reception 900102 (ou 900104) · supplier ... · supplier lot ... · PO ...". |
| Abrir MO7 | Barris 900102-3 e 900102-4 (GAGNON), 900104-4 (CANTONS, C-2124) e 900106-1 (TREMBLAY, T-118). O barril T-140 (900106-3), devolvido pelo gosto de bourgeon, **não** aparece. |
| Card *Uses* | "No production order used this lot." (lata é produto final). |
| Card *Customers* | DISTRIB-CHAUDIERE *Invoice* 6, 364 UN; LAURENTIAN-HOTELS *Invoice* 8, 200 UN; EPICERIE-STDENIS *Invoice* 9, 200 UN. |
| Card *Stock on hand* | MAPLE-SYRUP-540 MO8, 236 UN em FG-06. |
| Card *Stock movements* | *Receipt* Production 8 (1000) e as saídas das faturas 6 (364), 8 (200) e 9 (200). O número abre o movimento. |

## 3. De frente para trás: um barril até os clientes (SYRUP-BULK-AMB 900102-1)

| O que ver | Esperado |
|---|---|
| *Product* SYRUP-BULK-AMB | Lista *Lot* com os barris; os já usados aparecem com 0 em mão (900102-1 — 2028-03-23 · 0). 900102-4 tem 95 e 900106-2 tem 276. |
| Card *Origin* de 900102-1 | "Received 2026-09-10 · Reception 900102 · supplier GAGNON — Érablière Gagnon et fils · supplier lot B-0412 / récolte 2026-03-24 · PO 810102 · 275 KG". O link abre a recepção. |
| Card *Uses* | Order 1 *Closed* used 275 KG → made 1000 KG: SYRUP-STD MO1, que foi usado pelas ordens 2 (latas MO2), 3 (beurre MO3), 4 (bonbons MO4), 5 (sucre à la crème MO5) e 8 (latas MO8). Cada link abre a ordem. |
| Números do alto | *Lots reached* 7, *Customers* 4, *Stock lines* 2, *Open orders* 0. |
| *Lots reached* (linha sob a caixa amarela) | SYRUP-BULK-AMB 900102-1, SYRUP-STD MO1, MAPLE-SYRUP-540 MO2, MAPLE-BUTTER-200 MO3, MAPLE-CANDY-12 MO4, MAPLE-FUDGE-250 MO5, MAPLE-SYRUP-540 MO8, todos *Released*. |
| Card *Customers* | Os 4 clientes do demo, com todas as faturas de 1 a 9 que levaram esses lotes. |
| Card *Stock on hand* | MAPLE-CANDY-12 MO4 22 UN em FG-03 e MAPLE-SYRUP-540 MO8 236 UN em FG-06. |
| Card *Stock movements* | *Receipt* Reception 900102 (275, BAR-01) e *Issue* Production 1 (275). |

O botão para segurar os lotes do recall está no roteiro de qualidade.

## 4. Outro exemplo: sucre à la crème MO5 (com crème e beurre)

| Passo | Esperado |
|---|---|
| *Product* MAPLE-FUDGE-250, *Lot* MO5 | *Origin*: "Made 2026-10-08 · Order 5 · 300 UN", com SYRUP-STD MO1 (e seus barris), CREAM-35 900105-1 (LAITERIE, LT-80213-1) e BUTTER 900105-2 (LAITERIE, LT-80213-2). |
| Card *Customers* | BOUTIQUE-VQ (faturas 2 e 7), DISTRIB-CHAUDIERE (3) e EPICERIE-STDENIS (5): *Customers* 3. A nota de crédito NC-1 não aparece, porque foi só de preço (nada voltou ao estoque). |
| Caixa | MO5 não tem mais estoque: *Stock lines* 0. |

## 5. Nota de crédito com volta ao estoque

| Passo | Esperado |
|---|---|
| **Sales > Invoices**, fatura 8 (LAURENTIAN-HOTELS), **Credit note**: deixar só MAPLE-SYRUP-540 com qty 4 e *Return* marcado, **Save**, **Post** | Nota de crédito NC-2, total 39,60. As 4 latas voltam para MO8 em FG-06. |
| Voltar para MAPLE-SYRUP-540 MO8 | Em *Customers*, nova linha LAURENTIAN-HOTELS *Credit note* NC-2 com -4 UN. *Stock on hand*: MO8 240 UN. *Customers* continua 3. *Stock movements*: novo ajuste ADJ +4, SO NC-2. |

## 6. Exportar para Excel

| Passo | Esperado |
|---|---|
| **Export to Excel** (MAPLE-SYRUP-540 MO8) | Baixa `trace-MAPLE-SYRUP-540-MO8.xlsx` e a mensagem "The spreadsheet is being downloaded." |
| Abrir o arquivo | Abas *Summary*, *Origin*, *Uses*, *Customers*, *Stock*, *Movements*, com os mesmos dados da tela; a primeira linha em negrito e fixa. |
| Botão **FR** e exportar de novo | Arquivo em francês: abas *Résumé*, *Origine*, *Utilisations*, *Clients*, *Stock*, *Mouvements*. |

## 7. Acesso e recusas

| O que fazer | Esperado |
|---|---|
| Perfil sem *Lots and traceability* (Administration > Roles) | O item some do menu; pela API `/api/traceability` responde 403. |
| Perfil PRODUCTION do demo | Vê a tela (a rastreabilidade em si nunca altera nada). |
| Pela API, lote que não existe: `/api/traceability?product=SYRUP-BULK-AMB&lot=XYZ` | 404 "This lot is not in the stock of this product." |
| Matéria sem lote (CAN-540, LABEL) | Não aparece na origem das latas MO8: só as matérias controladas por lote são rastreadas. |
| Celular (tela estreita) | Os números ficam em 2 colunas e nada sai da tela. |

## 8. Ajuda

| Passo | Esperado |
|---|---|
| **Help > Production > Lots and traceability** (EN e FR) | Seções: Product, Lot, The recall summary, Origin, Uses, Customers, Stock on hand, Open production orders, Stock movements, Export to Excel. |
