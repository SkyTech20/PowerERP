# PowerERP — Status de lote e não conformidades: roteiro de testes

Roteiro para testar o menu **Quality** (passo 5 do plano SCOR / ISO): **Quality > Lot status** (liberar, segurar, pôr em quarentena ou rejeitar um lote) e **Quality > Nonconformances** (registrar um problema, segurar o lote, fechar com a decisão e a ação corretiva), mais o botão de segurar os lotes de um recall em **Production > Lots and traceability**. Um lote que não está liberado não sai em fatura de venda nem em ordem de produção. Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**. Os valores esperados são os do cenário **Maple products** logo depois de restaurar o demo.

**Antes de começar:** entre como administrador, vá em **Administration > System settings**, escolha o cenário **Maple products** e restaure os dados de demo. O demo já traz 3 não conformidades (a 1 e a 2 fechadas, a 3 aberta), o lote de bonbons MO9 segurado e o barril 900106-3 rejeitado; a nova não conformidade deste roteiro será a 4.

---

## 1. A tela Lot status

**Quality > Lot status**

| Passo | Esperado |
|---|---|
| Abrir a tela | 4 quadros no alto: *On hold* 1, *Quarantine* 0, *Rejected* 1, *Released* 14. Lista dos lotes: produto e descrição, lote com a validade embaixo, quantidade com o depósito/local embaixo e *Status*. No topo, os que pedem decisão: MAPLE-CANDY-12 MO9 *On hold* (amarelo, motivo "Order 9, step 10/20 Cook to 115 °C: 118.5 °C") e SYRUP-BULK-AMB 900106-3 *Rejected* (0, devolvido ao fornecedor, motivo "NC 1 closed: return to supplier"). |
| **?** | Abre a ajuda da tela; os filtros e os campos têm seu **?**. |
| Filtro *Product* SYRUP-BULK-AMB | 900106-3 *Rejected*, 900102-4 95 KG em PLANT/BAR-04 e 900106-2 276 KG em PLANT/BAR-10, os dois *Released*. Voltar para *All*. |
| Busca "TANK" | Só SYRUP-STD MO7, 146 KG em PLANT/TANK-02. Apagar a busca. |

## 2. Não conformidade de recepção (segura o lote)

Situação: a análise de laboratório do barril B-0431 da Érablière Gagnon (lote 900102-4, ainda com 95 kg em BAR-04) deu chumbo acima do limite. O barril já foi usado em parte no sirop padronizado MO7.

**Quality > Nonconformances**, **New**

| Passo | Esperado |
|---|---|
| Abrir | *Date found* hoje, *Found at* Internal check, *Severity* Minor, *Hold the lot* marcado, *Disposition* To decide. |
| **Save** sem nada | Erro em *What is wrong* (obrigatório). |
| *Found at* Reception, *Document* REC 900102, *Severity* Critical, *Product* SYRUP-BULK-AMB, *Lot* 900102-4, *Quantity affected* 95, *What is wrong* "Lab analysis of barrel B-0431: lead 0.6 ppm, limit 0.5 ppm", **Save** | "Created." Nonconformance 4 — SYRUP-BULK-AMB · 900102-4, selo *Open*. *Lot status*: On hold. *Unit*: KG. Card *History*: Created; Lot put on hold. |
| **Quality > Lot status** | Quadro *On hold* 2. SYRUP-BULK-AMB 900102-4 no topo, linha amarela, *On hold*, motivo "NC 4: Lab analysis of barrel B-0431...", embaixo admin, data e o link *Nonconformance 4*. |
| **History** na linha | Released → On hold, quem, quando e o motivo. **Hide history** fecha. |

## 3. Recall: segurar os lotes feitos com o barril

| Passo | Esperado |
|---|---|
| Na linha 900102-4, **Trace** | Abre **Production > Lots and traceability** com SYRUP-BULK-AMB 900102-4. Card "Status of this lot: *On hold* · Lot status". Números: *Lots reached* 6, *Customers* 4, *Stock lines* 6, *Open orders* 1 (a ordem 9 *Completed*). |
| *Lots reached* | SYRUP-BULK-AMB 900102-4 *On hold*, SYRUP-STD MO7 *Released*, MAPLE-SYRUP-540 MO8 *Released*, MAPLE-CANDY-12 MO9 *On hold*, MAPLE-FUDGE-250 MO10 *Released*, MAPLE-BUTTER-200 MO11 *Released*. |
| Card *Customers* | DISTRIB-CHAUDIERE (fatura 6), LAURENTIAN-HOTELS (8), EPICERIE-STDENIS (9) e BOUTIQUE-VQ (7). |
| Clicar o botão **Put the 4 released lot(s) on hold** sem motivo | Aviso "Write the reason of the change." |
| *Reason* "Barrel 900102-4 (B-0431): lead above the limit (NC 4)", botão | "4 lot(s) put on hold." MO7, MO8, MO10 e MO11 passam a *On hold*; o card diz "Every lot the recall reaches is already held back." |
| **Quality > Lot status** | *On hold* 6, *Rejected* 1, *Released* 9. |

## 4. Lote segurado não sai

| Passo | Esperado |
|---|---|
| **Sales > Invoices**, rascunho de DISTRIB-CHAUDIERE, **Check** | *To fix before posting*: "MAPLE-SYRUP-540 200 UN > 0 UN" e "MAPLE-FUDGE-250 60 UN > 0 UN". **Post** recusa com "Not enough released stock: lots on hold, in quarantine or rejected cannot go out (Quality > Lot status)." A fatura continua rascunho. |
| **Production > Production orders**, **New**: MAPLE-SYRUP-540 100 UN, **Save** | Ordem 14. Na lista de materiais, SYRUP-STD 72 KG com *Available* 0 (o MO7 segurado não conta). |
| **Release**, **Issue** | Erro de SYRUP-STD: "Not enough released stock..." (72 > 0 KG). A ordem 12 já liberada também não consegue tirar o sirop. (Cancele a ordem 14.) |
| **Inventory > Stock movements**, transferir SYRUP-BULK-AMB 900102-4 de BAR-04 para um local vazio (por exemplo BAR-12) | Funciona: o lote segurado ainda pode ser movido, ajustado ou contado no estoque. |

## 5. Fechar a não conformidade

**Quality > Nonconformances**, abrir a 4

| Passo | Esperado |
|---|---|
| **Close** (confirmar) sem decisão | Erro em *Disposition* (obrigatório). |
| *Disposition* Return to supplier, **Close** | Erro em *Corrective action* (obrigatório). |
| *Root cause* "Old evaporator pan at the sugar bush (lead solder).", *Corrective action* "Return the barrel to Érablière Gagnon; ask for a lead analysis with every barrel.", **Close**, confirmar | "Nonconformance closed." Selo *Closed*, campos só leitura, *Lot status* Rejected, *Closed by* / *Closed on* preenchidos. *History*: Closed (Return to supplier), Lot rejected, Lot put on hold, Created. Botões: **Back to list** e **Reopen** (não há Save nem Delete). |
| **Quality > Lot status** | SYRUP-BULK-AMB 900102-4 *Rejected*, motivo "NC 4 closed: return to supplier". Os lotes feitos com ele continuam *On hold*: cada um pede a sua decisão (seção 6). |
| **Quality > Nonconformances** (lista) | 1 *Closed* (Reception, 900106-3, Return to supplier), 2 *Closed* (Customer, MAPLE-FUDGE-250 MO5, Use as is), 3 *Open* (Production, MAPLE-CANDY-12 MO9) e 4 *Closed*, *Critical*, Reception, SYRUP-BULK-AMB, 900102-4, *Rejected*, 95 KG, Return to supplier. Filtros *Status*, *Found at*, *Severity*, *Product*. |
| Abrir a 4, **Reopen**, motivo "More barrels of B-04xx to check" | "Nonconformance reopened." Selo *Open*, campos editáveis de novo; o lote continua *Rejected*. Feche de novo com Return to supplier. |

Regras das disposições ao fechar: **Use as is** libera o lote (só se foi esta NC que o segurou); **Scrap** e **Return to supplier** rejeitam; **Rework** deixa em espera.

## 6. Mudar o status à mão

**Quality > Lot status**

| Passo | Esperado |
|---|---|
| Na linha MAPLE-SYRUP-540 MO8, **Change status** | Abre embaixo: *New status* (os outros 3 status), *Reason*, **Save**, **Cancel** e a explicação. |
| **Save** sem motivo | "Write the reason of the change." |
| *Quarantine*, motivo "Cans sent to the lab for lead", **Save** (ou Enter) | "Lot MO8: Quarantine." Quadros: *Quarantine* 1, *On hold* 4. |
| **Change status** de novo: *Released*, motivo "Lab result: lead 0.02 ppm, conform", **Save** | MO8 *Released*; desce para o fim da lista (os lotes que pedem decisão vêm primeiro). **History** mostra as 3 mudanças. |
| Rascunho de DISTRIB-CHAUDIERE, **Check** | Só sobra o problema do sucre à la crème (MO10 ainda segurado). |
| Quadro *Rejected* | Filtra só os rejeitados (900106-3 e 900102-4). Clicar de novo tira o filtro. Filtro *Status* "Not released" mostra on hold + quarantine + rejected. |

## 7. Perfis

| Passo | Esperado |
|---|---|
| **Administration > Roles**, perfil PRODUCTION | Módulo *Quality*: Lot status (View, Change status) e Nonconformances (View, Create, Edit, Close). |
| Perfil WAREHOUSE | Lot status View; Nonconformances View e Create. |
| Entrar com um usuário WAREHOUSE | Vê **Quality > Lot status** sem o botão *Change status*; na rastreabilidade (se tiver acesso) não aparece o botão de segurar. Pode criar uma NC mas não vê **Close**. |
| **Administration > Audit log** | As mudanças aparecem: Change status (Lot status), Create / Edit / Close (Nonconformances). |

## 8. Francês

| Passo | Esperado |
|---|---|
| Botão **FR** | Menu **Qualité > Statut des lots / Non-conformités**; status *Libéré, En attente, Quarantaine, Rejeté*; traitements *Utiliser tel quel, Retouche, Rebut, Retour au fournisseur*. A ajuda abre em francês. |
