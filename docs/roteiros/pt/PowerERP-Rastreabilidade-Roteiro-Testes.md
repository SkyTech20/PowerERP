# PowerERP — Lotes e rastreabilidade: roteiro de testes

Roteiro para testar a tela **Production > Lots and traceability** (passo 3 do plano SCOR / ISO): de um lote, ver de onde veio (fornecedor, lote do fornecedor, pedido de compra; para um lote fabricado, os lotes das matérias), para onde foi (ordens de produção, lotes feitos com ele, clientes), o que um recall precisa alcançar e exportar tudo para Excel. Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**. Os valores esperados são os do cenário **Pastry shop** depois dos preparativos da seção 1.

**Antes de começar:** entre como administrador, vá em **Administration > System settings**, escolha o cenário **Pastry shop** e restaure os dados de demo.

---

## 1. Preparar: fabricar e vender

| Passo | Esperado |
|---|---|
| **Production > Production orders**, **New**: DOUGH, 10 KG, **Save**, **Release** | Ordem 1 liberada. |
| Card *Shop floor*: **Issue**; depois *Quantity made* 9,8 e **Report** | Ordem 1 *In progress*, lote feito MO1 (9,8 KG). |
| **New**: PASTEL-HAM-CHEESE, 40 UN, **Save**, **Release**, **Issue**, *Quantity made* 40, **Report** | Ordem 2 *In progress*. Em *Lots used*: DOUGH MO1 2,4 KG, HAM 900104-1 1,6 KG, CHEESE 900104-2 1,6 KG. Lote feito MO2 (40 UN). |
| **Sales > Invoices**, **New**: CAFE-PLATEAU, PASTEL-HAM-CHEESE 100 UN, **Save**, **Post** | Fatura 1. A saída segue o FEFO: 45 de HAM-CHEESE-20261118, 45 de HAM-CHEESE-20261119 e 10 de MO2. |
| **New**: TRAITEUR-ROYAL, PASTEL-HAM-CHEESE 15 UN, **Save**, **Post** | Fatura 2, os 15 saem de MO2. |

## 2. A tela

**Production > Lots and traceability**

| Passo | Esperado |
|---|---|
| Abrir a tela | Listas *Product* e *Lot* e a mensagem "Pick a product and a lot to see its trace." A lista *Lot* fica desativada até escolher o produto. |
| Abrir a lista *Product* | Só produtos com lote no estoque: BEEF-RAW, CHEESE, CHICKEN-RAW, DOUGH, EGG, HAM, PASTEL-... Produtos sem lote, como FLOUR, não aparecem. |
| Escolher HAM | Como só há um lote, ele já vem escolhido: 900104-1 — 2027-01-11 · 13,4. A rastreabilidade aparece na hora. O endereço passa a ser `#/prod/traceability/HAM/900104-1` (dá para guardar ou mandar). |
| **?** | Abre a ajuda da tela; cada campo tem seu **?**. |

## 3. Um passo para trás e um para frente (HAM 900104-1)

| O que ver | Esperado |
|---|---|
| Os 4 números do alto | *Lots reached* 2, *Customers* 2, *Stock lines* 2, *Open orders* 1. |
| Caixa amarela | "For a recall: 2 lot(s) reached, 2 customer(s) to call, 2 stock line(s) to put on hold and 1 open order(s) to check." |
| Card *Origin* | "Received 2026-11-12 · Reception 900104 · supplier DELIQC — Distribution Fromages et Charcuteries QC · supplier lot DEL-261112-1 · PO 800104 · 15 KG". O link abre a recepção. |
| Card *Uses* | Order 2 *In progress* used 1,6 KG → made 40 UN: PASTEL-HAM-CHEESE lote MO2. O link abre a ordem. |
| Card *Customers* | "Lots reached: HAM 900104-1, PASTEL-HAM-CHEESE MO2". CAFE-PLATEAU, *Invoice* 1, MO2, 10 UN; TRAITEUR-ROYAL, *Invoice* 2, MO2, 15 UN. |
| Card *Stock on hand* | HAM 900104-1 13,4 KG em COLD-01; PASTEL-HAM-CHEESE MO2 15 UN em REC. |
| Card *Open production orders* | Order 2 *In progress*. |
| Card *Stock movements* | Movimento *Receipt* da Reception 900104 (15) e *Issue* Production 2 (1,6). O número abre o movimento. |

## 4. De trás para frente (lote fabricado MO2)

| Passo | Esperado |
|---|---|
| *Product* PASTEL-HAM-CHEESE, *Lot* MO2 | Os lotes do dia 18 e 19 aparecem com 0 em mão; MO2 com 15. |
| Card *Origin* | "Made 2026-11-25 · Order 2 · 40 UN". Abaixo, cada lote usado: DOUGH MO1 (feito pela Order 1), HAM 900104-1 e CHEESE 900104-2, cada um até a recepção e o lote do fornecedor (DEL-261112-1, DEL-261112-2). |
| Card *Uses* | "No production order used this lot." |
| Números do alto | *Lots reached* 1, *Customers* 2, *Stock lines* 1, *Open orders* 1. |
| Card *Stock movements* | *Receipt* Production 2 (40), *Issue* Invoice 1 (10), *Issue* Invoice 2 (15). |

## 5. Nota de crédito

| Passo | Esperado |
|---|---|
| **Sales > Invoices**, fatura 2, **Credit note**, deixar 5 UN com *Return* marcado, **Save**, **Post** | Nota de crédito NC-1; 5 UN voltam para MO2. |
| Voltar para MO2 | Em *Customers*, nova linha TRAITEUR-ROYAL *Credit note* NC-1 com -5 UN. *Stock on hand*: MO2 20 UN. *Customers* continua 2 (TRAITEUR-ROYAL ainda tem 10). |

## 6. Exportar para Excel

| Passo | Esperado |
|---|---|
| **Export to Excel** (HAM 900104-1) | Baixa `trace-HAM-900104-1.xlsx` e a mensagem "The spreadsheet is being downloaded." |
| Abrir o arquivo | Abas *Summary*, *Origin*, *Uses*, *Customers*, *Stock*, *Movements*, com os mesmos dados da tela; a primeira linha em negrito e fixa. |
| Botão **FR** e exportar de novo | Arquivo em francês: abas *Résumé*, *Origine*, *Utilisations*, *Clients*, *Stock*, *Mouvements*. |

## 7. Acesso e recusas

| O que fazer | Esperado |
|---|---|
| Perfil sem *Lots and traceability* (Administration > Roles) | O item some do menu; pela API `/api/traceability` responde 403. |
| Perfil PRODUCTION do demo | Vê a tela (só leitura: a tela nunca altera nada). |
| Pela API, lote que não existe: `/api/traceability?product=HAM&lot=XYZ` | 404 "This lot is not in the stock of this product." |
| Matéria sem lote (FLOUR) | Não aparece na origem do DOUGH MO1: só as matérias controladas por lote são rastreadas. |
| Celular (tela estreita) | Os números ficam em 2 colunas e nada sai da tela. |

## 8. Ajuda

| Passo | Esperado |
|---|---|
| **Help > Production > Lots and traceability** (EN e FR) | Seções: Product, Lot, The recall summary, Origin, Uses, Customers, Stock on hand, Open production orders, Stock movements, Export to Excel. |
