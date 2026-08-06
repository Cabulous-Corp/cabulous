# Modernização da página de login

## Objetivo

Substituir o layout atual do login por uma experiência moderna, limpa e consistente com os primitives padrão do shadcn/ui, mantendo o fluxo de autenticação existente e todo o texto visível em português do Brasil.

## Escopo

Incluído:

- Novo layout responsivo dividido em painel de marca e painel de autenticação.
- Uso dos primitives existentes `Card`, `Input`, `FormLabel`, `FormMessage` e `Button`.
- Remoção completa do fundo de triângulos, timers, geração aleatória e estilos específicos associados a ele.
- Animações CSS discretas de entrada e brilho ambiental, com suporte a `prefers-reduced-motion`.
- Correção do texto da interface para pt-BR com acentuação.
- Preservação do `loginAction`, das validações, do link de recuperação e do redirecionamento após autenticação.
- Testes E2E para renderização, responsividade, acessibilidade básica e submissão do formulário.

Fora do escopo:

- Mudanças na API, no backend ou no contrato de autenticação.
- Criação de cadastro, login social ou alteração do fluxo de recuperação de senha.
- Criação de novos primitives shadcn ou instalação de dependências.
- Reformulação global do tema da aplicação.

## Direção visual

O desktop terá duas colunas dentro de uma composição centralizada e limitada por largura:

1. Painel de marca à esquerda, com gradiente roxo discreto, identidade “Cabulous”, a mensagem “Conecte-se ao que importa.” e uma forma luminosa estática ou suavemente pulsante.
2. Painel de autenticação à direita, usando um `Card` claro ou escuro conforme o tema, título “Entrar”, texto de apoio, campos rotulados, link de recuperação e botão primário.

Em telas menores, o painel de marca será reduzido e ficará acima do formulário. A composição não poderá criar rolagem horizontal nem depender de alturas fixas que escondam o botão em telas curtas.

## Comportamento

- O campo de identificação aceitará e-mail ou usuário e será rotulado como “E-mail ou usuário”.
- O campo de senha continuará exigindo pelo menos oito caracteres.
- Mensagens de validação usarão português brasileiro e aparecerão associadas aos respectivos campos.
- O botão exibirá “Entrando...” durante a ação e ficará desabilitado enquanto a requisição estiver em andamento.
- Erros retornados pelo servidor continuarão aparecendo no formulário sem perder os valores digitados.
- Sucesso continuará redirecionando para `/`.
- A animação de entrada não poderá bloquear foco, interação ou leitura por tecnologias assistivas.
- Quando `prefers-reduced-motion: reduce` estiver ativo, as animações serão desabilitadas ou reduzidas a transições instantâneas.

## Arquitetura e arquivos

- `app/web/app/(auth)/layout.tsx`: simplificar o wrapper de autenticação para fornecer apenas a superfície de página e o fundo base.
- `app/web/app/(auth)/login/page.tsx`: reescrever a composição visual mantendo o estado e a chamada de autenticação atuais.
- `app/web/app/(auth)/login/_components/AnimatedTrianglesBackground.tsx`: remover, pois a animação atual será substituída por CSS local ao layout.
- `app/web/e2e/smoke.spec.ts`: atualizar locators e acrescentar as verificações de layout responsivo e de conteúdo pt-BR.

Não serão alterados `actions/session.ts`, `lib/api/auth.ts` ou o backend.

## Critérios de aceitação

- A página exibe painel dividido no desktop e composição empilhada no mobile.
- O formulário usa os estilos padrão dos primitives shadcn existentes, sem transparências acidentais ou componentes customizados desnecessários.
- Não existe referência ao componente de triângulos nem a timers de animação aleatória.
- Todos os textos visíveis do login estão em pt-BR e com acentuação correta.
- Os campos possuem labels acessíveis, mensagens de erro associadas e foco visível.
- A submissão continua chamando o backend e tratando estados de carregamento, erro e sucesso.
- Não há overflow horizontal em viewport de desktop ou de 390px.
- Lint, typecheck, build, testes unitários e teste E2E do login passam.

