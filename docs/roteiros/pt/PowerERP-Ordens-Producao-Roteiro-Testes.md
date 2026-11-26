# PowerERP — Ordens de produção (M3a e M3b): roteiro de testes

Roteiro para testar as ordens de produção: criar a partir da receita aprovada, ver materiais, disponibilidade e custo, liberar, voltar a rascunho e cancelar (M3a); depois o chão de fábrica: consumir os materiais por lote, apontar a produção com lote novo, devolver, ver a genealogia, concluir e fechar com o custo real (M3b, seções 9 a 13). Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**. Os valores esperados são os do cenário **Maple products** logo depois de restaurar o demo, feitos em 2026-11-26 (os custos não dependem da data).

**Antes de começar:** entre como administrador, vá em **Administration > System settings**, escolha o cenário **Maple products** e restaure os dados de demo. O demo já traz as ordens 1 a 13 de outubro e novembro (10 fechadas, a 9 concluída, a 12 liberada e a 13 em rascunho): as ordens criadas neste roteiro começam na 14.

---

## 1. Nova ordem

**Production > Production orders**

| Passo | Esperado |
|---|---|
| Abrir a tela | As 13 ordens do demo, filtros *Status*, *Product* e *Warehouse*. |
| **New** | Card *What to make*, *Start* = hoje. Os cards de materiais dizem "Pick a product to see the materials of its recipe." |
| Abrir a lista *Product* | Só produtos com receita aprovada: MAPLE-BUTTER-200, MAPLE-CANDY-12, MAPLE-FUDGE-250, MAPLE-SYRUP-250, MAPLE-SYRUP-540 e SYRUP-STD. Matérias-primas como SYRUP-BULK-AMB não aparecem. |
| Escolher MAPLE-CANDY-12 | Sem digitar nada mais: *Quantity to make* 100 (quantidade base da receita), *Unit* UN, *Warehouse* PLANT, *Revision* A ★. |
| Card *Materials* | Alerta verde "All the materials are available": SYRUP-STD 14 KG (disponível 146), BOX-12 100 UN (disponível 112), LABEL 100 UN. |
| Card *Operations and cost* | 2 operações (MPL-COOK, MPL-MOULD). Tempo total 85 min, *Estimated cost* 195,53 $, custo por unidade 1,9553 / UN. |
| Mudar *Quantity to make* para 200 e sair do campo | Tudo recalcula: SYRUP-STD 28 KG, BOX-12 200 UN, LABEL 200 UN; alerta amarelo de falta: BOX-12 falta 88 UN (vermelho); tempo 105 min; custo estimado 357,47 $. |
| **Save** | Mensagem *Created*. Ordem 14, badge *Draft*. Card *Tracking* com *Created by* e *Created on*. Card *History* com "Created". |

## 2. Recusas

Numa ordem nova:

| O que fazer | Esperado |
|---|---|
| **Save** sem produto | "This field is required" em *Product*. |
| MAPLE-CANDY-12, *Quantity to make* 0, **Save** | "Must be greater than zero." |
| *Start* 2026-12-10 e *Due* 2026-12-01 | "The end is before the start." em *Due*. |
| Pela API, `POST /api/production-orders` com `cProduct` SYRUP-BULK-AMB | 400 *no_approved_recipe* (produto comprado, sem receita). |

## 3. Liberar

Na ordem 14:

| Passo | Esperado |
|---|---|
| **Release** e confirmar | Mensagem *Order released*. Badge *Released*, tela em leitura, *Released by* e *Released on* preenchidos. |
| Card *History* | "Created" e "Released" (Draft → Released). |
| Botões | **Back to draft** e **Cancel order**. Sem **Save** nem **Delete**. |
| A falta de BOX-12 | Continua no card *Materials*: falta avisa, não bloqueia. |

## 4. Voltar a rascunho e cancelar

| Passo | Esperado |
|---|---|
| **Back to draft**, motivo "trocar quantidade" | Badge *Draft*, campos editáveis, *Released by/on* somem. Histórico com o motivo. |
| Mudar para 100 e **Save** | Materiais e custo recalculados (195,53 $), alerta verde. |
| **Cancel order**, motivo "sem caixas" | Badge *Cancelled*, tela em leitura, sem botões de ação. Histórico com 4 linhas. |
| Lista com filtro *Status* = Cancelled | A ordem 14. |

## 5. Apagar e numeração

| Passo | Esperado |
|---|---|
| Criar a ordem 15 (SYRUP-STD, 100 KG) | Todos os materiais disponíveis: SYRUP-BULK-AMB 101 KG (disponível 371), FILTER-PAPER 0,5 UN. Custo estimado 807,64 $. |
| **Delete** na ordem 15 | Some da lista. |
| Criar outra ordem | Recebe o número 16: números não se repetem. |

## 6. Ligações com outras telas

| Passo | Esperado |
|---|---|
| **Inventory > Items**, tentar apagar BOX-12 | Recusado: o produto é usado. |
| **Production > Recipes**, MAPLE-CANDY-12 A, **Make obsolete**; depois **Release** da ordem 13 (rascunho de MAPLE-CANDY-12) | "This product has no approved recipe." A ordem fica em rascunho. (Restaurar o demo depois.) |

## 7. Permissões

| Passo | Esperado |
|---|---|
| **Administration > Roles**, perfil PRODUCTION | *Production orders* em *Full*, com a ação *Release*. |
| Perfil SALES | Sem acesso: a entrada não aparece no menu de quem tem esse perfil. |
| Perfil personalizado com *Production orders* em *Edit* (sem *Release*) | Cria e altera rascunhos, mas os botões **Release**, **Back to draft** e **Cancel order** não aparecem. |

## 9. Consumir os materiais (M3b)

Restaure o demo. Crie uma ordem de SYRUP-STD, 100 KG (ordem 14), **Save** e **Release**.

| Passo | Esperado |
|---|---|
| Card *Shop floor*, parte *1. Issue the materials* | SYRUP-BULK-AMB 101 KG, com *To issue* já preenchido. O FILTER-PAPER é *backflush*: sai sozinho quando a produção é apontada. |
| **Show the lots** | "Ready: the stock is there." e a tabela, na ordem FEFO (vence antes, sai antes): 95 KG do barril 900102-4 (BAR-04) e 6 KG do barril 900106-2 (BAR-10). Nada se move (confira em **Inventory > Stock movements**). |
| **Issue** | Mensagem *Materials issued*. Badge *In progress*. Histórico com "Production started". Coluna *Issued* do card *Materials* preenchida. |
| Card *Lots made and lots used* | Em *Lots used*: 2 linhas *Issue* com valor (701,46 $ e 44,30 $) e o número do movimento; o clique abre o movimento. |
| **Inventory > Stock movements** | 2 saídas com documento *Production* 14. |
| **Issue** de novo | Erro "Nothing to issue: every material is issued, or the quantities are empty." |

## 10. Apontar a produção

| Passo | Esperado |
|---|---|
| Parte *2. Report the production*: *Quantity made* 99; deixar *Lot*, *Expiry* e *Location* em automático; **Report** | Mensagem *Production reported*. Em *Lots made*: lote MO14, 99 KG, em REC (o sirop padronizado não tem localização padrão), validade 2027-11-26 (365 dias), custo unitário 8,0764, valor 799,56 $. Para pôr numa cuba, digite *Location* TANK-01 (vazia) antes do **Report**. |
| Card *Tracking* | *Lot made* MO14 e *Quantity made* 99. |
| **Inventory > Stock on hand**, SYRUP-STD | Lote MO14 com 99 KG, além do MO7 (146 KG em TANK-02). |
| Lista das ordens | Coluna *Made* com 99 KG. |

## 11. Devolver um material

| Passo | Esperado |
|---|---|
| Em *Lots used*, linha do barril 900106-2, **Return**, digitar 2 | Mensagem de devolução. Nova linha *Return* com -2 KG e -14,77 $. *Issued* de SYRUP-BULK-AMB = 99 KG. O barril volta para BAR-10. |
| **Return** de 50 KG na mesma linha | Erro "More than what went out of the stock for this line." (sobram 4 KG desse barril). |

## 12. Concluir e fechar

| Passo | Esperado |
|---|---|
| Card *Actual cost* | Materiais 732,35 $, operações 59,90 $ (para 99 KG), custo real 792,25 $, por unidade 8,0025 / KG, estimado 8,0764 / KG, variação -7,32 $ (verde). |
| **Complete** e confirmar | Badge *Completed*. O card *Shop floor* some. Botões **Reopen** e **Close**. |
| **Reopen** | Volta a *In progress*. **Complete** de novo. |
| **Close** e confirmar | Badge *Closed*, sem botões. *Actual cost* diz "Kept when the order was closed". Histórico: Created, Released, Production started, Completed, Reopened, Completed, Closed. |
| **Cancel order** numa ordem que já moveu estoque | Não aparece; pela API a resposta é 409. |
| Ordens do demo (ex.: a 4, MAPLE-CANDY-12) | Já fechadas com o custo real: 388 caixas feitas de 400, nota "12 boîtes de bonbons cassés au démoulage." |

## 13. Regras do estoque e recusas

| O que fazer | Esperado |
|---|---|
| Ordem de MAPLE-FUDGE-250 100 UN liberada, **Show the lots** | A crème sai do lote 900107-1: o lote 900105-1 (12 L) venceu em 2026-10-27 e nunca é usado. A manteiga sai 1 KG do lote 900105-2 (vence antes) e 0,5 KG do 900107-2. |
| Na mesma ordem, *To issue* de SYRUP-STD 500 | **Show the lots** lista o problema "Not enough stock available" (500 > 146 KG); **Issue** recusa e nada se move. |
| **Issue** normal e **Complete** sem apontar nada | "Report a quantity made before completing the order." |
| Ordem em rascunho | O card *Shop floor* não aparece. |
| Perfil sem a ação *Shop floor* (Administration > Roles) | O card *Shop floor* e os botões **Return** não aparecem. |

## 14. Ajuda

| Passo | Esperado |
|---|---|
| Botão **?** na tela | Painel com a ajuda de *Production orders* (EN/FR). |
| Ícone ⓘ ao lado de cada campo | Explica o campo. |
