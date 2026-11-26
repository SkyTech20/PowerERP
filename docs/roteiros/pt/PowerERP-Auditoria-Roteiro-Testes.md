# PowerERP — Auditoria e log de segurança: roteiro de testes


Roteiro para testar o passo 4 do plano SCOR / ISO: o **bloqueio de login** depois de tentativas erradas, o **desbloqueio** pelo administrador e a tela **Administration > Audit log** (quem fez o quê e quando: logins, bloqueios, recusas e cada alteração). Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**. Vale para qualquer cenário de demo.

**Antes de começar:** entre como administrador (admin).

---

## 1. Criar um usuário de teste

| Passo | Esperado |
|---|---|
| **Administration > Users & security**, **New**: *Username* marie, *Full name* Marie Tremblay, *Role* SALES, *New password* secret1, **Save** | Usuário criado. A lista tem a coluna nova *Locked* (vazia). |
| **Production > Production orders**, **New**: SYRUP-STD, 100 KG (ou PAIN-BL-675 no demo Manufacturing), **Save**, **Release** | Ordem liberada. Isso vai aparecer no log. |
| **Sign out** | Volta para a tela de login. |

## 2. Bloqueio depois de 5 senhas erradas

| Passo | Esperado |
|---|---|
| Entrar como marie com uma senha errada, 4 vezes | "Wrong username or password, or the user is inactive." a cada vez. |
| 5ª senha errada | "Too many failed sign-ins: this account is locked for 15 min. Try again later, or ask the administrator to unlock it." |
| Agora a senha certa (secret1) | A mesma mensagem: bloqueado, mesmo com a senha certa. |
| Uma senha errada para um usuário que não existe (ex.: ghost) | "Wrong username or password..." (não diz se o usuário existe). |

## 3. Desbloquear

| Passo | Esperado |
|---|---|
| Entrar como admin; **Administration > Users & security** | marie com o selo vermelho *Locked* (passe o mouse: até que horas). |
| Abrir marie | Aviso amarelo "Locked after too many failed sign-ins (until ...): Unlock lets the user sign in now." e o botão **Unlock**. |
| **Unlock** | Mensagem "The user can sign in again."; o aviso e o botão somem; na lista, *Locked* fica vazio. |
| Sair e entrar como marie / secret1 | Entra. |
| Contagem zera: como marie, 1 senha errada e depois a certa; sair e errar 1 vez de novo | Não bloqueia (o bloqueio é para 5 erradas **seguidas**). |

## 4. Recusa de acesso

| Passo | Esperado |
|---|---|
| Como marie (perfil SALES), digitar no endereço `#/admin/audit` | Volta para o painel: a tela não é dela. |
| Pela API, como marie: `/api/audit` | 403. Fica no log como *Access refused*. |

## 5. A tela Audit log

Entrar como admin. **Administration > Audit log**.

| O que ver | Esperado |
|---|---|
| Abrir a tela | *From* = hoje − 6 dias, *To* vazio. O mais recente em cima. 50 por página. |
| Linhas de marie | *Sign-in failed* (vermelho, linha rosa) com "wrong password" embaixo, 5 vezes; *Account locked*; *Refused: locked*; *Unlocked*; *Signed in*; *Access refused*. |
| Linha *Sign-in failed* de ghost | Usuário ghost, motivo "unknown user". |
| **Details** de *Account locked* | `attempts: 5`, `minutes: 15`. **Hide** fecha. |
| **Details** de *Unlocked* | `by: admin`. |
| Linhas de admin | *Create* em *Users & security* (fiche marie): **Details** mostra o que foi enviado, com `password: "***"`. *Create* e *Release* em *Production orders* (número da ordem): **Details** de *Create* mostra o produto e a quantidade enviados. |
| Abaixo de cada usuário | O endereço IP. |
| Nenhuma senha | Nenhuma linha nem detalhe mostra secret1 ou as senhas erradas digitadas. |

## 6. Filtros

| Passo | Esperado |
|---|---|
| *User* marie | Só os eventos de marie. |
| *Kind* Security | Só logins, bloqueios, desbloqueios, senhas e recusas. A lista *Event* mostra só eventos de segurança. |
| *Kind* Change, *Event* Release | Só a liberação da ordem. |
| Pesquisa: o número da ordem | A criação e a liberação dessa ordem. |
| *From* 2000-01-01, *To* 2000-01-02 | "No event for these filters." |
| Cálculos não entram | Abrir uma ordem em rascunho e mudar a quantidade (o ERP recalcula): nenhuma linha nova. Só o **Save** gera *Edit*. |

## 7. Exportar e idioma

| Passo | Esperado |
|---|---|
| **Export to Excel** | Baixa `audit-log.xlsx` com os eventos dos filtros, a primeira linha em negrito e fixa, datas em UTC. |
| Botão **FR** | Tela em francês ("Journal d'audit", "Connexion refusée", "mauvais mot de passe"); o Excel sai com cabeçalhos em francês. |

## 8. Senha própria

| Passo | Esperado |
|---|---|
| Como marie, **My account**: senha atual errada | Erro na tela; no log, *Password change refused*. |
| Senha atual certa e nova senha | No log, *Password changed*. |

## 9. Ajuda

| Passo | Esperado |
|---|---|
| **?** na tela Audit log, e **Help > Administration > Audit log** (EN e FR) | Seções From, To, User, Kind, Event, Search, Columns, Export to Excel, The lockout. |
| **Help > Users & security** | Nova seção *Unlock*. |
