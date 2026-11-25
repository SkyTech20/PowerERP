# PowerERP — Ordens de produção (M3a): roteiro de testes

Roteiro para testar as ordens de produção: criar a partir da receita aprovada, ver materiais, disponibilidade e custo, liberar, voltar a rascunho e cancelar. O estoque ainda não se move nesta etapa (consumo e apontamento vêm no M3b). Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**. Os valores esperados são os do cenário **Pastry shop** logo depois de restaurar o demo.

**Antes de começar:** entre como administrador, vá em **Administration > System settings**, escolha o cenário **Pastry shop** e restaure os dados de demo. O demo começa sem ordens.

---

## 1. Nova ordem

**Production > Production orders**

| Passo | Esperado |
|---|---|
| Abrir a tela | Lista vazia, filtros *Status*, *Product* e *Warehouse*. |
| **New** | Card *What to make*, *Start* = hoje. Os cards de materiais dizem "Pick a product to see the materials of its recipe." |
| Abrir a lista *Product* | Só produtos com receita aprovada (BOILED-EGG, DOUGH, PASTEL-BEEF, PASTEL-CHICKEN...). Matérias-primas como FLOUR não aparecem. |
| Escolher PASTEL-BEEF | Sem digitar nada mais: *Quantity to make* 100 (quantidade base da receita), *Unit* UN, *Warehouse* KITCHEN (padrão do produto), *Revision* A ★. |
| Card *Materials* | Alerta amarelo de falta. DOUGH 6 KG, disponível 0, falta 6 KG (vermelho); FILL-BEEF-EGG 8 KG, falta 8 KG; OIL-FRY 2 L, disponível 60 L ✓; PAPER-BAG 100 UN, disponível 2 000 UN ✓. |
| Card *Operations and cost* | 3 operações (PST-SHAPE, PST-FRY, PST-PACK). Tempo total 80 min, *Estimated cost* 60,07 $, custo por unidade 0,6007 / UN. |
| Mudar *Quantity to make* para 200 e sair do campo | Tudo recalcula: DOUGH 12 KG, FILL-BEEF-EGG 16 KG, OIL-FRY 4 L, PAPER-BAG 200 UN; tempo 135 min (2,25 h); custo estimado 110,13 $. |
| **Save** | Mensagem *Created*. Ordem 1, badge *Draft*. Card *Tracking* com *Created by* e *Created on*. Card *History* com "Created". |

## 2. Recusas

Numa ordem nova:

| O que fazer | Esperado |
|---|---|
| **Save** sem produto | "This field is required" em *Product*. |
| PASTEL-BEEF, *Quantity to make* 0, **Save** | "Must be greater than zero." |
| *Start* 2026-12-10 e *Due* 2026-12-01 | "The end is before the start." em *Due*. |
| Pela API, `POST /api/production-orders` com `cProduct` FLOUR | 400 *not_made* (produto comprado). |

## 3. Liberar

Na ordem 1:

| Passo | Esperado |
|---|---|
| **Release** e confirmar | Mensagem *Order released*. Badge *Released*, tela em leitura, *Released by* e *Released on* preenchidos. |
| Card *History* | "Created" e "Released" (Draft → Released). |
| Botões | **Back to draft** e **Cancel order**. Sem **Save** nem **Delete**. |
| A falta de DOUGH | Continua no card *Materials*: falta avisa, não bloqueia. |

## 4. Voltar a rascunho e cancelar

| Passo | Esperado |
|---|---|
| **Back to draft**, motivo "trocar quantidade" | Badge *Draft*, campos editáveis, *Released by/on* somem. Histórico com o motivo. |
| Mudar para 150 e **Save** | Materiais e custo recalculados. |
| **Cancel order**, motivo "sem massa" | Badge *Cancelled*, tela em leitura, sem botões de ação. Histórico com 4 linhas. |
| Lista com filtro *Status* = Cancelled | A ordem 1. |

## 5. Apagar e numeração

| Passo | Esperado |
|---|---|
| Criar a ordem 2 (DOUGH, 10 KG) | Todos os materiais disponíveis: alerta verde "All the materials are available". Custo estimado 20,77 $. |
| **Delete** na ordem 2 | Some da lista. |
| Criar outra ordem | Recebe o número 3: números não se repetem. |

## 6. Ligações com outras telas

| Passo | Esperado |
|---|---|
| **Inventory > Items**, tentar apagar PAPER-BAG | Recusado: o produto é usado por uma ordem. |
| **Production > Recipes**, PASTEL-BEEF A, **Make obsolete**; depois tentar **Release** de uma ordem rascunho de PASTEL-BEEF | "This product has no approved recipe." A ordem fica em rascunho. (Restaurar o demo depois.) |

## 7. Permissões

| Passo | Esperado |
|---|---|
| **Administration > Roles**, perfil PRODUCTION | *Production orders* em *Full*, com a ação *Release*. |
| Perfil SALES | Sem acesso: a entrada não aparece no menu de quem tem esse perfil. |
| Perfil personalizado com *Production orders* em *Edit* (sem *Release*) | Cria e altera rascunhos, mas os botões **Release**, **Back to draft** e **Cancel order** não aparecem. |

## 8. Ajuda

| Passo | Esperado |
|---|---|
| Botão **?** na tela | Painel com a ajuda de *Production orders* (EN/FR). |
| Ícone ⓘ ao lado de cada campo | Explica o campo. |
