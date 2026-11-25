# PowerERP — Recepção com entrada no estoque: roteiro de testes

Roteiro para testar a entrada da recepção no estoque, com lote, lote do fornecedor, validade e localização. Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**. Os valores esperados são os do cenário **Pastry shop** logo depois de restaurar o demo.

**Antes de começar:** entre como administrador, vá em **Administration > System settings**, escolha o cenário **Pastry shop** e restaure os dados de demo. Restaurar de novo volta tudo ao estado inicial.

---

## 1. Recepções antigas já estão no estoque

**Purchasing > Receptions**

| Passo | Esperado |
|---|---|
| Ver a coluna *In stock* da lista | As 6 recepções do demo (900101 a 900106) mostram *In stock*. |
| Abrir a 900102 (MEATCO) | Badge *In stock*, tudo em leitura. Nas linhas: lote 900102-1 e 900102-2, lote do fornecedor MEA-261110-1 e MEA-261110-2, validade 2027-05-09, localização COLD-01. |
| Card *Put into the stock* | Dois movimentos (BEEF-RAW 40, CHICKEN-RAW 50) com valor. Clicar no número abre o movimento em **Inventory > Stock movements**. |
| Filtro *In stock* = No | Lista vazia. |

## 2. Receber o pedido em aberto 800107

| Passo | Esperado |
|---|---|
| **New**, *Reception number* 900107, *PO number* 800107 | Fornecedor MEATCO e duas linhas preenchidos: BEEF-RAW 40 e CHICKEN-RAW 50. |
| *Warehouse* KITCHEN | |
| Na linha 1, *Supplier lot* MC-88231; na linha 2, MC-88232. Deixar *Lot*, *Expiry* e *Location* vazios | O campo *Lot* mostra "Automatic". |
| **Save** | Badge *Not in stock yet*. |
| **Check** | Card *What goes into the stock* com "Ready: nothing to fix". Linha 1: lote 900107-1, validade = data da recepção + 180 dias, localização REC. Linha 2: lote 900107-2, REC. |
| Por que REC e não COLD-01? | COLD-01 já tem outro lote desses produtos e a regra é um lote por localização. O ERP usa então a localização de recepção da cozinha. |
| **Inventory > Stock on hand**, filtrar BEEF-RAW | Ainda só o lote 900102-1: o Check não muda nada. |

## 3. Pôr no estoque

| Passo | Esperado |
|---|---|
| **Put in stock** e confirmar | Mensagem *Reception put in stock*. Badge *In stock*, tela em leitura, *Put in stock on* e *Put in stock by* preenchidos. |
| Card *Put into the stock* | 2 movimentos, BEEF-RAW 40 (580,00) e CHICKEN-RAW 50 (340,00). |
| **Inventory > Stock on hand**, BEEF-RAW | Novo lote 900107-1 em REC, 40 KG, com a validade. |
| **Inventory > Stock movements**, último movimento | Tipo *Receipt*, documento *Reception* 900107, motivo MEATCO, comentário "PO 800107 · MC-88231". |
| Tentar apagar a recepção 900107 | O botão não aparece. Pela API a resposta é 409 *posted*. |

## 4. Problemas que bloqueiam

Crie a recepção 900108 sobre o PO 800107, warehouse KITCHEN:

| Linha | O que digitar | Esperado no **Check** |
|---|---|---|
| 1 | BEEF-RAW, qty 20, *Location* COLD-01 | "Line 1 (BEEF-RAW): This location already holds another lot..." porque a localização foi digitada. Apague a localização e o ERP escolhe outra. |
| 2 | Item XYZ-99, qty 1 | "Line 2 (XYZ-99): This code does not exist. — Item". |
| 3 | Sem item, descrição Transport, qty 1, custo 25 | Aparece em cinza: "No item: not stocked". Não é problema. |

**Put in stock** recusa com a primeira mensagem e nada entra no estoque. Corrija (apague a localização da linha 1 e a linha 2) e ponha no estoque.

## 5. Permissão

**Administration > Roles**: o perfil **WAREHOUSE** tem *Post* em Receptions. Crie um perfil com Receptions só em *Edit*: o usuário vê **Check**, mas não vê **Put in stock**.

## 6. Ajuda

Na recepção, clique **?**: a página explica a vida da recepção, cada coluna nova (Supplier lot, Lot, Expiry, Location, Serial no.) e os botões Check e Put in stock. O mesmo em FR.
