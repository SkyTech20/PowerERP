# PowerERP — Recepção com entrada no estoque: roteiro de testes

Roteiro para testar a entrada da recepção no estoque, com lote, lote do fornecedor, validade e localização. Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**. Os valores esperados são os do cenário **Maple products** logo depois de restaurar o demo.

**Antes de começar:** entre como administrador, vá em **Administration > System settings**, escolha o cenário **Maple products** e restaure os dados de demo. Restaurar de novo volta tudo ao estado inicial.

No demo, cada barril de sirop d'érable é um lote e fica na sua localização (BAR-01 a BAR-12): a regra do ERP é um lote de um produto por localização.

---

## 1. Recepções antigas já estão no estoque

**Purchasing > Receptions**

| Passo | Esperado |
|---|---|
| Ver a coluna *In stock* da lista | As 7 recepções do demo (900101 a 900107) mostram *In stock*. |
| Abrir a 900102 (GAGNON, Érablière Gagnon et fils) | Badge *In stock*, tudo em leitura. Quatro barris SYRUP-BULK-AMB: lotes 900102-1 a 900102-4, lote do fornecedor "B-0412 / récolte 2026-03-24", "B-0418 / récolte 2026-03-29", "B-0425 / récolte 2026-04-02" e "B-0431 / récolte 2026-04-08" (número do barril do produtor e data da colheita), validades 2028-03-23 a 2028-04-07, localizações BAR-01 a BAR-04. |
| Card *Put into the stock* | Quatro movimentos com valor: 2 035,00, 1 983,20, 2 079,40 e 1 998,00. Clicar no número abre o movimento em **Inventory > Stock movements**. |
| Abrir a 900106 (TREMBLAY) | O comentário "Baril T-118 : 266 kg reçus sur 280 kg commandés." e a linha 1 com 280 pedidos e 266 recebidos. |
| Filtro *In stock* = No | Lista vazia. |

## 2. Receber o pedido em aberto 810108

O pedido 810108 (GAGNON) tem 4 barris de sirop ambré de 275 kg.

| Passo | Esperado |
|---|---|
| **New**, *Reception number* 900108, *PO number* 810108 | Fornecedor GAGNON e quatro linhas SYRUP-BULK-AMB de 275 KG preenchidos. |
| *Warehouse* PLANT | |
| Em cada linha, o *Supplier lot* do barril: B-0510, B-0514, B-0519, B-0523. Deixar *Lot*, *Expiry* e *Location* vazios | O campo *Lot* mostra "Automatic". |
| **Save** | Badge *Not in stock yet*. |
| **Check** | Card *What goes into the stock*: lotes 900108-1 a 900108-4, validade = data da recepção + 730 dias, localização REC em todas. Problema nas linhas 2, 3 e 4: "This location already holds another lot of this product: one lot per product per location." |
| Por que? | O sirop em vrac não tem localização padrão, então o ERP propõe a localização de recepção (REC) para todos os barris, e REC só pode ter um lote do produto. |
| Digitar a *Location* de cada barril: BAR-01, BAR-02, BAR-03 e BAR-07 (estão vazias), **Save**, **Check** | "Ready: nothing to fix. Click Put in stock." |
| **Inventory > Stock on hand**, filtrar SYRUP-BULK-AMB | Ainda só os lotes 900102-4 (BAR-04, 95 KG) e 900106-2 (BAR-10, 276 KG): o Check não muda nada. |

A validade proposta conta da data da recepção. Para usar a data da colheita, digite a *Expiry* (colheita + 2 anos) em cada linha antes de pôr no estoque.

## 3. Pôr no estoque

| Passo | Esperado |
|---|---|
| **Put in stock** e confirmar | Mensagem *Reception put in stock*. Badge *In stock*, tela em leitura, *Put in stock on* e *Put in stock by* preenchidos. |
| Card *Put into the stock* | 4 movimentos SYRUP-BULK-AMB de 275 KG a 7,40, cada um 2 035,00. |
| **Inventory > Stock on hand**, SYRUP-BULK-AMB | Os novos lotes 900108-1 a 900108-4 em BAR-01, BAR-02, BAR-03 e BAR-07. |
| **Inventory > Stock movements**, último movimento | Tipo *Receipt*, documento *Reception* 900108, motivo GAGNON, comentário "PO 810108 · B-0523". |
| **Production > Lots and traceability**, SYRUP-BULK-AMB, lote 900108-1 | *Origin*: recepção 900108, fornecedor GAGNON, lote do fornecedor B-0510, PO 810108. |
| Tentar apagar a recepção 900108 | O botão não aparece. Pela API a resposta é 409 *posted*. |

## 4. Problemas que bloqueiam

Restaure o demo e crie a recepção 900109 sobre o PO 810108, warehouse PLANT:

| Linha | O que digitar | Esperado no **Check** |
|---|---|---|
| 1 | SYRUP-BULK-AMB, qty 100, *Location* BAR-04 | "Line 1 (SYRUP-BULK-AMB): This location already holds another lot..." porque BAR-04 tem o barril 900102-4. Escolha uma localização vazia (ex.: BAR-08). |
| 2 | Item XYZ-99, qty 1 | "Line 2 (XYZ-99): This code does not exist. — Item". |
| 3 | Sem item, descrição Transport, qty 1, custo 25 | Aparece em cinza: "No item: not stocked". Não é problema. |

**Put in stock** recusa com a primeira mensagem e nada entra no estoque. Corrija (localização da linha 1 e apague a linha 2) e ponha no estoque.

## 5. Permissão

**Administration > Roles**: o perfil **WAREHOUSE** tem *Post* em Receptions. Crie um perfil com Receptions só em *Edit*: o usuário vê **Check**, mas não vê **Put in stock**.

## 6. Ajuda

Na recepção, clique **?**: a página explica a vida da recepção, cada coluna nova (Supplier lot, Lot, Expiry, Location, Serial no.) e os botões Check e Put in stock. O mesmo em FR.
