# PowerERP — Extrato de movimentos (fiche de stock): roteiro de testes

Roteiro para testar o extrato de uma linha de **Inventory > Stock on hand**: ao clicar na linha, o ERP mostra todos os movimentos daquele produto, naquele warehouse, location, lote e número de série, do mais antigo ao mais recente, com entrada, saída, saldo após cada movimento e o documento de origem (recepção, ordem de produção, fatura, nota de crédito, inventário). A tela do produto continua acessível pelo código do produto na lista e pelo botão **Open the product** no extrato. Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**. Os valores esperados são os do cenário **Maple products** logo depois de restaurar o demo.

**Antes de começar:** entre como administrador, vá em **Administration > System settings**, escolha o cenário **Maple products** e restaure os dados de demo.

---

## 1. Da lista para o extrato

**Inventory > Stock on hand**

| Passo | Esperado |
|---|---|
| Passar o mouse numa linha | A linha inteira fica destacada (clicável). O código do produto aparece como link. |
| Clicar no **código** MAPLE-SYRUP-540 | Abre a tela do produto (como antes). Voltar com o navegador. |
| Clicar em outra parte da linha MAPLE-SYRUP-540 / FG-06 / MO8 (por exemplo na coluna *Location*) | Abre o extrato. O endereço fica `#/inv/stock/card/MAPLE-SYRUP-540/PLANT/FG-06/MO8/-` (o `-` é o número de série vazio). |

## 2. O extrato das latas MO8

| O que ver | Esperado |
|---|---|
| Topo | "Stock on hand /" (link de volta para a lista), título **MAPLE-SYRUP-540 — Amber maple syrup, 540 ml can**, botões **?**, **Open the product** e **Trace the lot**. |
| Card de dados | *Warehouse / location* PLANT — Usine de transformation - Saint-Georges / FG-06, *Lot* MO8, *Expiry date* 2028-11-02. |
| Números | *On hand* 236 UN, *Reserved* 0 UN, *Available* 236 UN. |
| Tabela *Movements* (4 movimentos) | 2026-11-03 *Made by a production order* · Order 8 · entrada 1,000 · saldo 1,000 |
| | 2026-11-06 *Invoice* · Invoice 6 · DISTRIB-CHAUDIERE · saída −364 · saldo 636 |
| | 2026-11-18 *Invoice* · Invoice 8 · LAURENTIAN-HOTELS · saída −200 · saldo 436 |
| | 2026-11-20 *Invoice* · Invoice 9 · EPICERIE-STDENIS · saída −200 · saldo 236 |
| Última linha | *Balance today* 236 UN (igual ao *On hand* da lista). |
| Clicar em **Order 8** | Abre a ordem de produção 8. Voltar. |
| Clicar em **Invoice 6** | Abre a fatura 6 de DISTRIB-CHAUDIERE. Voltar. |
| Clicar em **movement #…** abaixo de uma data | Abre o movimento em **Inventory > Stock movements**. Voltar. |
| **Open the product** | Abre o produto MAPLE-SYRUP-540. |
| **Trace the lot** | Abre **Production > Lots and traceability** no lote MO8. |

## 3. Período (From / To)

| Passo | Esperado |
|---|---|
| *From* = 2026-11-10 | Primeira linha: *Opening balance (movements before this date)* 636. Depois só as faturas 8 e 9; última linha *Balance today* 236. Aparece o botão **All dates** e o contador "2 movement(s)". |
| *To* = 2026-11-18 | Só a fatura 8; última linha *Balance at the end of the period* 436. |
| *From* = 2026-12-01, *To* vazio | "No movement between these dates."; abertura e saldo final 236. |
| **All dates** | Volta aos 4 movimentos. |

## 4. Um barril de matéria-prima (recepção e consumo)

Na lista, clicar na linha **SYRUP-BULK-AMB / BAR-04 / lote 900102-4**.

| O que ver | Esperado |
|---|---|
| Movimentos | 2026-09-10 *Reception* · Reception 900102 · entrada 270 · saldo 270; 2026-11-02 *Used by a production order* · Order 7 · SYRUP-STD · saída −175 · saldo 95. |
| Clicar em **Reception 900102** | Abre a recepção 900102. |
| Números | *On hand* 95 KG. |

## 5. Movimentos novos aparecem no extrato

| Passo | Esperado |
|---|---|
| Em **Inventory > Stock movements**, novo movimento *Reservation* de 10 UN de MAPLE-SYRUP-540, PLANT / FG-06, lote MO8 | Gravado. |
| Abrir o extrato de MO8 de novo | Nova linha *Reservation (Manual)*: saldo continua 236 e embaixo dele aparece "reserved 10". *Reserved* 10 UN, *Available* 226 UN. |
| Novo movimento *Transfer* de 6 UN de MAPLE-SYRUP-540 lote MO8, de PLANT / FG-06 para uma location vazia de produtos acabados | Gravado. No extrato de FG-06: *Transfer to PLANT / …* saída −6, saldo 230. Na lista, a nova linha da location destino abre um extrato com *Transfer from PLANT / FG-06* entrada 6. |

## 6. Ajuda e francês

| Passo | Esperado |
|---|---|
| **?** no extrato | Abre a ajuda de *Stock on hand*, com a seção **Stock card** (colunas, From, To). Os ícones ⓘ ao lado de *From* e *To* abrem o texto de cada campo. |
| Botão **FR** | Título "Fiche de stock…", colunas *Date, Quoi, Document, Client / fournisseur / note, Entrée, Sortie, Solde, Coût unitaire, Valeur, Utilisateur*; tipos *Fabriqué par un ordre de production*, *Facture*... |
| Celular (tela estreita) | Os três números ficam lado a lado; a tabela rola na horizontal. |

## 7. Acesso

| Passo | Esperado |
|---|---|
| Usuário com perfil que tem **Stock on hand** mas não **Products** | A linha abre o extrato; o código do produto não é link e o botão **Open the product** não aparece. Documentos de telas sem acesso aparecem como texto, sem link. |
| Usuário sem **Stock on hand** | Abrir o endereço do extrato leva ao Dashboard. |
