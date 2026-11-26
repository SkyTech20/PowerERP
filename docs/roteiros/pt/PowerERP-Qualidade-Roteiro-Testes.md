# PowerERP — Status de lote e não conformidades: roteiro de testes

Roteiro para testar o menu **Quality** (passo 5 do plano SCOR / ISO): **Quality > Lot status** (liberar, segurar, pôr em quarentena ou rejeitar um lote) e **Quality > Nonconformances** (registrar um problema, segurar o lote, fechar com a decisão e a ação corretiva), mais o botão de segurar os lotes de um recall em **Production > Lots and traceability**. Um lote que não está liberado não sai em fatura de venda nem em ordem de produção. Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**. Os valores esperados são os do cenário **Pastry shop** depois dos preparativos da seção 1.

**Antes de começar:** entre como administrador, vá em **Administration > System settings**, escolha o cenário **Pastry shop** e restaure os dados de demo.

---

## 1. Preparar: fabricar e vender

| Passo | Esperado |
|---|---|
| **Production > Production orders**, **New**: DOUGH, 10 KG, **Save**, **Release**, **Issue**, *Quantity made* 9,8, **Report** | Ordem 1, lote feito MO1. |
| **New**: PASTEL-HAM-CHEESE, 40 UN, **Save**, **Release**, **Issue**, *Quantity made* 40, **Report** | Ordem 2, usa HAM 900104-1 e faz o lote MO2 (40 UN). |
| **Sales > Invoices**, **New**: CAFE-PLATEAU, PASTEL-HAM-CHEESE 100 UN, **Save**, **Post** | Fatura postada; sobram 30 UN de MO2. |

## 2. A tela Lot status

**Quality > Lot status** (o menu **Quality** é novo, abaixo de Production)

| Passo | Esperado |
|---|---|
| Abrir a tela | 4 quadros no alto: *On hold* 0, *Quarantine* 0, *Rejected* 0, *Released* 11. Lista dos lotes em estoque: produto e descrição, lote com a validade embaixo, quantidade com o depósito/local embaixo, *Status* (todos *Released*, verde). |
| **?** | Abre a ajuda da tela; os filtros e os campos têm seu **?**. |
| Filtro *Product* HAM | Só HAM 900104-1, 13,4 KG em KITCHEN/COLD-01. Voltar para *All*. |
| Busca "COLD" | Os lotes de COLD-01. Apagar a busca. |

## 3. Não conformidade na recepção (segura o lote)

**Quality > Nonconformances**, **New**

| Passo | Esperado |
|---|---|
| Abrir | *Date found* hoje, *Found at* Internal check, *Severity* Minor, *Hold the lot* marcado, *Disposition* To decide. |
| **Save** sem nada | Erro em *What is wrong* (obrigatório). |
| *Found at* Reception, *Document* REC 900104, *Severity* Critical, *Product* HAM, *Lot* 900104-1, *Quantity affected* 13,4, *What is wrong* "Temperature 9 °C at reception, limit 4 °C", **Save** | "Created." Nonconformance 1 — HAM · 900104-1, selo *Open*. *Lot status*: On hold. *Unit*: KG. Card *History*: Created; Lot put on hold. |
| **Quality > Lot status** | Quadro *On hold* 1. HAM 900104-1 no topo, linha amarela, *On hold*, motivo "NC 1: Temperature 9 °C...", embaixo admin, data e o link *Nonconformance 1*. |
| **History** na linha | Released → On hold, quem, quando e o motivo. **Hide history** fecha. |

## 4. Recall: segurar os lotes feitos com o presunto

| Passo | Esperado |
|---|---|
| Na linha HAM, **Trace** | Abre **Production > Lots and traceability** com HAM 900104-1. Novo card: "Status of this lot: *On hold* · Lot status". Em *Customers*, os lotes alcançados mostram o status: HAM *On hold*, PASTEL-HAM-CHEESE MO2 *Released*. |
| Clicar o botão **Put the 1 released lot(s) on hold** sem motivo | Aviso "Write the reason of the change." |
| *Reason* "Ham lot 900104-1 too warm at reception (NC 1)", botão | "1 lot(s) put on hold." MO2 passa a *On hold*; o card diz "Every lot the recall reaches is already held back." |

## 5. Lote segurado não sai

| Passo | Esperado |
|---|---|
| **Sales > Invoices**, **New**: CAFE-PLATEAU, PASTEL-HAM-CHEESE 10 UN, **Save**, **Post** | Erro: "Not enough released stock: lots on hold, in quarantine or rejected cannot go out (Quality > Lot status)." A fatura continua rascunho. (Apague a fatura.) |
| **Production > Production orders**, **New**: PASTEL-HAM-CHEESE 40 UN, **Save** | Na lista de materiais, HAM com *Available* 0 (o lote segurado não conta). |
| **Release**, **Issue** | Erro de HAM: "Not enough released stock...". (Cancele a ordem.) |
| **Inventory > Stock movements**, transferir HAM 900104-1 de COLD-01 para outro local | Funciona: o lote segurado ainda pode ser movido, ajustado ou contado no estoque. |

## 6. Fechar a não conformidade

**Quality > Nonconformances**, abrir a 1

| Passo | Esperado |
|---|---|
| **Close** (confirmar) sem decisão | Erro em *Disposition* (obrigatório). |
| *Disposition* Scrap, **Close** | Erro em *Corrective action* (obrigatório). |
| *Root cause* "The supplier truck refrigeration was off.", *Corrective action* "Probe every delivery of meat at reception; refuse above 4 °C.", **Close**, confirmar | "Nonconformance closed." Selo *Closed*, campos só leitura, *Lot status* Rejected, *Closed by* / *Closed on* preenchidos. *History*: Closed (Scrap), Lot rejected, Lot put on hold, Created. Botões: **Back to list** e **Reopen** (não há Save nem Delete). |
| **Quality > Lot status** | HAM 900104-1 *Rejected*, motivo "NC 1 closed: scrap". |
| **Quality > Nonconformances** (lista) | Nonconformance 1 *Closed*, *Critical*, Reception, HAM, 900104-1, *Rejected*, 13,4 KG, Scrap. Filtros *Status*, *Found at*, *Severity*, *Product*. |
| Abrir a 1, **Reopen**, motivo "More boxes to check" | "Nonconformance reopened." Selo *Open*, campos editáveis de novo; o lote continua *Rejected*. Feche de novo com Scrap. |

Regras das disposições ao fechar: **Use as is** libera o lote (só se foi esta NC que o segurou); **Scrap** e **Return to supplier** rejeitam; **Rework** deixa em espera.

## 7. Mudar o status à mão

**Quality > Lot status**

| Passo | Esperado |
|---|---|
| Na linha PASTEL-HAM-CHEESE MO2, **Change status** | Abre embaixo: *New status* (os outros 3 status), *Reason*, **Save**, **Cancel** e a explicação. |
| **Save** sem motivo | "Write the reason of the change." |
| *Quarantine*, motivo "Sample sent to the lab", **Save** (ou Enter) | "Lot MO2: Quarantine." Quadros: *Quarantine* 1, *On hold* 0. |
| **Change status** de novo: *Released*, motivo "Lab result: conform", **Save** | MO2 *Released*; desce para o fim da lista (os lotes que pedem decisão vêm primeiro). **History** mostra as 3 mudanças. |
| Quadro *Rejected* | Filtra só os rejeitados (HAM). Clicar de novo tira o filtro. Filtro *Status* "Not released" mostra on hold + quarantine + rejected. |

## 8. Perfis

| Passo | Esperado |
|---|---|
| **Administration > Roles**, perfil PRODUCTION | Módulo *Quality*: Lot status (View, Change status) e Nonconformances (View, Create, Edit, Close). |
| Perfil WAREHOUSE | Lot status View; Nonconformances View e Create. |
| Entrar com um usuário WAREHOUSE | Vê **Quality > Lot status** sem o botão *Change status*; na rastreabilidade (se tiver acesso) não aparece o botão de segurar. Pode criar uma NC mas não vê **Close**. |
| **Administration > Audit log** | As mudanças aparecem: Change status (Lot status), Create / Edit / Close (Nonconformances). |

## 9. Francês

| Passo | Esperado |
|---|---|
| Botão **FR** | Menu **Qualité > Statut des lots / Non-conformités**; status *Libéré, En attente, Quarantaine, Rejeté*; traitements *Utiliser tel quel, Retouche, Rebut, Retour au fournisseur*. A ajuda abre em francês. |
