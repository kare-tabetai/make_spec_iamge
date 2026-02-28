# **Google Agent Development Kit (ADK) を活用したマルチエージェントシステム構築の包括的ガイド：環境構築から高度なプロトコル実装まで**

## **序論：自律型AIシステムのパラダイムシフト**

人工知能の応用領域は、単なるテキスト生成やチャットインターフェースとしての利用から、推論、計画、ツール操作、そして自律的な意思決定を行うエージェントシステムへと急速に進化している1。初期の生成AIアーキテクチャにおいては、単一の大規模言語モデル（LLM）に対してすべてのドメイン知識とタスク処理能力を要求する「モノリシック（一枚岩）なエージェント」のアプローチが主流であった3。しかしながら、このアプローチは複雑で多段階にわたる要求を処理する際、文脈の喪失や非関連情報の生成といった深刻な機能不全を引き起こす傾向がある3。

2025年4月に開催されたGoogle Cloud NEXTにおいて公式に発表されたAgent Development Kit（ADK）は、この課題に対する構造的な解決策を提供するオープンソースフレームワークである1。Googleの社内プロダクトであるAgentspaceやCustomer Engagement Suite (CES) を駆動する技術基盤と同一のアーキテクチャを採用しており、プロンプトエンジニアリングに依存した実験的な開発から、決定論的なオーケストレーションとフレームワーク駆動のアプローチへの移行を促進する1。本報告書は、ADKを利用したマルチエージェントシステムの環境構築手法、中核となる概念、実践的な設計パターン、および参考となる技術リソースを網羅的に分析し、高度な自律型エコシステムを構築するための専門的な洞察を提供する。

## **基本的な概念とアーキテクチャの原則**

マルチエージェントシステムの設計において、ADKはAIエージェントをソフトウェアエンジニアリングの対象として再定義する7。システムはモデル非依存（Model-agnostic）かつデプロイ環境非依存（Deployment-agnostic）であり、特定の基盤モデルに縛られることなく、局所的な環境からクラウド上の分散環境まで一貫した挙動を保証する1。

### **エージェントの構成要素と階層化構造**

ADKにおけるエージェントとは、指示を理解し、意思決定を行い、ツールを利用してユーザーや他のエージェントと対話する知的ユニットである1。エージェントの振る舞いは、システムプロンプトに相当する「指示（Instruction）」と、外部機能へのアクセスを提供する「ツール（Tools）」によって規定される1。

システムの複雑性を管理するため、ADKはエージェントを階層的なツリー構造で編成する10。この階層構造は、現実世界の組織におけるチーム構造に触発されたものであり、どのエージェントがどのアシスタントへタスクを委譲できるかを厳密に制御する10。この制御により、システム全体の情報の流れが予測可能となり、デバッグの容易さとモジュール性が飛躍的に向上する10。

### **エージェントの種別とルーティング戦略**

タスクの性質に応じて最適なプロセス制御を実現するため、ADKは複数のエージェントタイプを提供している11。推論の不確実性を伴う動的なタスクと、手順が厳密に定まった定型業務を適切に分離することが、堅牢なシステムの要件となる11。

| エージェント種別 | アーキテクチャ上の役割 | 推奨される適用シナリオ |
| :---- | :---- | :---- |
| **LlmAgent** | 言語モデルの推論能力を活用し、文脈に応じた動的な意思決定、ツールの選択、およびサブエージェントへのタスク委譲を行う9。 | ユーザー入力の意図解釈、非定型な質問応答、動的ルーティング（LlmAgent Transfer）11。 |
| **SequentialAgent** | 複数のエージェントを事前に定義された順序で直列に実行する。各エージェントは共有された状態（Session State）を通じてデータを引き継ぐ3。 | データ収集、分析、要約といった、先行タスクの結果が後続タスクに必須となる直線的なパイプライン3。 |
| **ParallelAgent** | 複数のエージェントを並行して実行する（ファンアウト）。実行時間の短縮とリソースの効率的利用を目的とする3。 | 複数の独立したデータソースへの同時検索（例：フライトとホテルの同時手配）、コードの並行レビュー3。 |
| **LoopAgent** | 特定の終了条件（Exit Condition）が満たされるまで、内部のサブエージェント群の実行を反復する。生成と検証のサイクルを形成する4。 | SQLクエリの生成と構文チェックの反復、品質基準を満たすまでのコンテンツ自己修正プロセス13。 |
| **CustomAgent** | 基底クラスを拡張し、LLMに依存しない独自のビジネスロジックや状態同期機構を実装する3。 | 複雑な外部システムとの状態同期、特定のフラグに基づくカスタムバリデーション3。 |

## **開発環境の構築方法**

ADKを用いたマルチエージェントシステムの開発を開始するためには、適切な言語ランタイムの準備、クラウドプロバイダーとの認証統合、およびプロジェクトの足場固め（スキャフォールディング）が必要となる。

### **ランタイム環境とパッケージ管理**

ADKはPython、Go、Java、TypeScriptといった複数のプログラミング言語をサポートしているが、本稿では最も広範なエコシステムを持つPython環境を基準に解説する2。安定した開発環境を構築するためには、Python 3.10以上のバージョンが要求される14。また、パッケージのインストール速度を大幅に向上（従来のpipと比較して10倍から100倍）させるため、モダンなPythonパッケージマネージャーである uv の利用が公式のサンプル等で推奨されている15。

開発者はプロジェクト用のディレクトリを作成し、隔離された仮想環境を構築することで、システム全体の依存関係の競合を回避する16。仮想環境の有効化後、中核となる google-adk ライブラリのインストールを行う18。さらに、高度な機能を利用する場合は、Vertex AI Agent Engineへのデプロイメントを支援する拡張パッケージ（agent\_engines）や、エージェント間通信プロトコルを有効化する拡張パッケージ（a2a）を追加でインストールする20。

### **認証基盤と環境変数の設定**

ADKがLLMの推論APIやクラウドインフラストラクチャと安全に通信するためには、厳密な認証設定が不可欠である。Google Cloudのサービスアカウントと連携するため、ローカル開発環境においてはGoogle Cloud CLIを用いたアプリケーションのデフォルト認証情報（Application Default Credentials）の取得処理を実行する21。

ランタイムの挙動は、プロジェクトのルートディレクトリに配置された .env ファイル、またはシステム環境変数を通じて制御される16。特に重要な環境変数として、Vertex AIの利用を明示する GOOGLE\_GENAI\_USE\_VERTEXAI、請求とリソースの紐付けを行う GOOGLE\_CLOUD\_PROJECT、およびリソースの地理的配置を指定する GOOGLE\_CLOUD\_LOCATION が挙げられる16。外部ツールを利用する際（例えばGoogle Maps API）には、該当するAPIキーも同様に環境変数としてセキュアに管理される22。

### **Agent Starter Packによる初期化**

ゼロからの設定に伴うオーバーヘッドを削減し、本番環境への移行を見据えた構造を即座に手に入れるため、ADKは agent-starter-pack という強力なCLIツールを提供している8。このツールを uvx agent-starter-pack create コマンドで起動すると、対話形式のプロンプトを通じてプロジェクトのテンプレート、利用するリージョン、およびCI/CDの構成（例：GitHub Actions）を選択できる23。このプロセスにより、Google Cloud上の必要なAPIが自動的に有効化され、ディレクトリ構造やインフラストラクチャのコード（Terraformなど）が生成されるため、開発者は直ちにエージェントのロジック実装に集中することが可能となる23。

## **基本的な使い方：協調的アーキテクチャの設計手法**

モノリシックなプロンプトから高度なマルチエージェントシステムへの移行は、一般に4つの段階的な設計ステップを経て実装される3。ここでは、旅行計画システムを例として、その進化の過程とコード構造の原則を詳述する。

### **ステップ1：スペシャリストエージェントへの分割**

第一の段階は、複雑なタスクの分解である。万能な単一エージェントを構築する代わりに、明確な単一の責務を持つ専門家（スペシャリスト）エージェントの集合体を定義する3。例えば、「航空券手配エージェント」、「ホテル手配エージェント」、「観光地推奨エージェント」をそれぞれ個別の LlmAgent としてインスタンス化する3。この設計により、プロンプトの複雑性が低下し、特定タスクにおけるLLMの推論精度が向上するだけでなく、システムの一部を改修する際に他の機能へ悪影響を及ぼすリスクを最小化できる10。

### **ステップ2：ディスパッチャーによるツール化の導入**

スペシャリストを単なる階層化によって親エージェント（Root Agent）のサブエージェントとして配置した場合、「プロジェクトマネージャーの欠如」というアーキテクチャ上の欠陥が露呈する3。親エージェントがサブエージェントに処理を委譲した瞬間、ユーザーへの応答責任が完全にサブエージェントに移譲され、複数ステップにまたがる対話の全体的な文脈が失われてしまうのである3。

この限界を克服するため、ADKではスペシャリストエージェントを親エージェントの「ツール」として変換するアプローチを採用する3。各スペシャリストを AgentTool としてラッピングし、親エージェントのツールボックスに格納することで、親エージェントはコーディネーターまたはディスパッチャーとしての地位を維持する3。ディスパッチャーはユーザーの意図を解釈し、必要な情報を収集するために各ツール（エージェント）を呼び出し、その結果を中央集権的に総合して最終回答を生成する3。

### **ステップ3：並列実行によるパフォーマンスの最適化**

航空券の検索とホテルの検索など、相互に依存関係を持たないタスクを直列に処理することは、システムのレイテンシを無駄に増加させる3。この課題に対し、ADKの ParallelAgent を導入することで、コンカレントな実行環境が提供される3。

システム全体のオーケストレーションは SequentialAgent によって統括され、その内部の特定のステップにおいて ParallelAgent が呼び出される構造となる3。並行処理の過程においてデータの競合（レースコンディション）を防止するため、各サブエージェントは共有セッション状態（Session State）内のそれぞれ一意のキー（例：security\_report、style\_reportなど）に対して明示的にデータを出力するよう設計される必要がある13。

### **ステップ4：フィードバックループと品質保証**

システムが自律的に出力の品質を管理するためには、生成と評価のサイクル、すなわちフィードバックループの構築が不可欠である3。これには、タスクを実行するエージェントとは別に、特定の基準に基づいて出力を監査するレビュアー（批評家）エージェントを設ける手法が取られる3。

例えば、生成役エージェントがデータを出力し、そのデータを読み取ったレビュアーエージェントが「合格（PASS）」または「不合格（FAIL）」の評価を下す3。LoopAgent はこの評価ステータスを監視し、合格条件が満たされるまで生成役エージェントにフィードバックを返し、修正作業を反復させる13。また、人間の介入が必要な高リスクな操作に対しては、処理を一時停止して承認を求めるツールを組み込むことで、システムの安全性を担保する13。

## **外部システムとの連携：Model Context Protocol (MCP)**

AIエージェントが現実世界で有用性を発揮するためには、社内データベース、ファイルシステム、あるいは外部APIといった動的なコンテキストへのアクセスが必須となる。しかし、LLMに対してデータベースへの生のSQL実行権限を与えることは、プロンプトインジェクションやデータ漏洩といった重大なセキュリティリスクをもたらす26。

この課題に対する標準的な解決策として、ADKはModel Context Protocol (MCP) との強固な統合を提供する9。MCPは、エージェントと外部データソースの間に位置するユニバーサルアダプターであり、エージェントに対して「事前定義された安全なツール」のみを公開する役割を担う26。これにより、コネクションプーリングによるデータベースの過負荷保護や、Identity Aware Proxy (IAP) およびSecret Managerを利用したゼロトラストセキュリティの実装が容易となる26。

### **MCPサーバーの統合実装**

ADKにおけるMCPの統合は、主に McpToolset クラスを通じて実現される22。エージェントは、このツールセットを介してローカルまたはリモートのMCPサーバーに接続し、サーバーが提供する機能群を自身のスキルセットとして動的に取り込む22。

統合の方式には、標準入出力（Stdio）を用いたプロセス間通信と、サーバー送信イベント（Server-Sent Events: SSE）を用いたネットワーク経由の通信が存在する22。例えば、Google Maps APIを利用した経路探索機能をエージェントに付与する場合、Node.jsベースのMCPサーバーを npx コマンド経由で呼び出す構成を取る22。この際、認証情報（APIキー）はサーバープロセスの環境変数として安全に渡され、エージェント自身はキーの存在を意識することなく抽象化されたツールを利用する22。

より高度な分散環境においては、FastMCPなどの軽量フレームワークを利用して外部サーバー上にツール群をホストし、ADKエージェントはSSEコネクション（SseServerParams）を通じて遠隔のツールをシームレスに呼び出すパターンが採用される28。

## **異機種システム間の協調：Agent-to-Agent (A2A) プロトコル**

マルチエージェントシステムの規模が拡大し、異なるベンダー、異なるクラウド環境、あるいは異なるフレームワーク（LangGraphやCrewAIなど）で構築されたエージェント同士が連携する必要が生じた際、単一のプロセス内での通信モデルは限界を迎える30。ADKは、Linux Foundationの管轄下にあるオープン標準であるAgent-to-Agent (A2A) Protocolをネイティブにサポートすることで、この相互運用性の課題を解決している31。

A2Aプロトコルは、エージェントが内部のメモリ状態やツールの実装詳細（知的財産）を秘匿したまま、標準化されたJSON-RPCベースのメッセージングを通じてタスクを依頼し、結果を共有するための普遍的な言語として機能する31。

### **リモートエージェントの公開（Provider）と消費（Consumer）**

A2Aプロトコルの実装は、サービスを提供する側の「公開（Exposing）」と、サービスを利用する側の「消費（Consuming）」という二つの側面に大別される34。

エージェントを公開する場合、ADKの to\_a2a() 関数を用いて既存のエージェントロジックをラップし、サーバー（Uvicornなど）上で起動する20。このプロセスにおいて、エージェントの能力、サポートされる入力形式、およびスキルの説明を記述した「エージェントカード（AgentCard）」が自動的に生成される20。このカードは /.well-known/agent-card.json という標準化されたエンドポイントでホストされ、他のエージェントに対する一種の自己紹介（Capability Discovery）として機能する20。

一方、公開されたエージェントを消費する側の親エージェントは、RemoteA2aAgent インターフェースを利用する34。開発者は、接続先のリモートエージェントのURLとエージェントカードのパスを指定するだけでよく、ネットワーク通信、プロトコルのシリアライゼーション、および状態の同期といった複雑な処理はすべてADKによって抽象化される20。その結果、ローカルに実装された関数ツールを呼び出すのと全く同じ開発体験で、遠隔地のLangGraphエージェントなどにタスクを委譲することが可能となる30。

特筆すべきセキュリティ上の考慮点として、外部から提供されるエージェントカードの内容を盲信してはならないという点が挙げられる35。悪意のあるエージェントがカードの説明文に細工を施し、それを受信したLLMにプロンプトインジェクション攻撃を仕掛けるリスクが存在するため、受信データの適切なバリデーションとサニタイズがシステム設計における必須要件となる35。

## **システムの評価と品質保証（Evaluation）**

従来のソフトウェア開発では、ユニットテストや結合テストによる確定的な「パス/フェイル」の判定がコードの安定性を保証してきた36。しかし、確率的な性質を持つLLMエージェントにおいては、この二元的なアプローチは不十分である36。プロトタイプを本番環境へと移行させるためには、最終的な出力結果の妥当性だけでなく、エージェントが解決策に至るまでに踏んだプロセス（意思決定、ツール選択、実行順序）を定性的に評価する強固な枠組みが必要となる36。

### **評価データセットとテスト構成**

ADKの評価フレームワークは、JSON形式のテストケース定義（.test.json）と、評価基準を定義する設定ファイル（test\_config.json）の二つのコンポーネントに依存している36。

テストケース定義には、ユーザーからの初期クエリ、ゴールに到達するために想定されるツール呼び出しのシーケンス（軌跡）、中間のエージェント応答、および最終的な期待されるテキスト回答がPydanticのデータモデルに従って記述される36。設定ファイルには、合格とみなすための具体的なしきい値が設定される。例えば、ツールの利用軌跡が完璧に一致すること（tool\_trajectory\_avg\_score: 1.0）や、最終回答と期待される回答とのROUGE類似度スコアが一定以上であること（response\_match\_score: 0.8）などが定義される38。

### **評価の実行とLLM-as-a-judgeの活用**

評価プロセスは、CLIツール（adk evalコマンド）を通じて自動的に実行される36。評価エンジン（AgentEvaluator）は、テスト対象のエージェントを隔離されたセッション内で起動し、外部ツールへの実際のアクセスを遮断してモックデータ（mock\_tool\_output）を返すことで、副作用を伴わずにエージェントの推論ロジック自体をテストする38。

また、人間による評価に代わるスケーラブルな手法として、Vertex AIの評価サービスと連携した「LLM-as-a-judge」アプローチが推奨される39。このプロセスでは、テストデータが存在しない「コールドスタート問題」を解決するため、専門家エージェントに完璧な解答ステップを作成させた後、テスト対象エージェントに同一タスクを実行させ、その不完全な軌跡をLLM裁判官が採点するという合成データを用いた自動化ワークフローが利用される39。これにより、CI/CDパイプラインへの評価機能の統合が可能となり、コードの変更に伴う品質の退行（リグレッション）を継続的に監視できる36。

## **本番環境へのデプロイメントとセキュリティモデル**

開発、テスト、および評価のフェーズを通過したエージェントは、スケーラビリティと可用性を備えた本番インフラストラクチャへと移行される2。ADKで構築されたシステムはコンテナ化が容易であり、組織の要件に応じた柔軟なデプロイメント戦略を採ることができる2。

| デプロイメント基盤 | アーキテクチャの特性 | セキュリティと認証モデル |
| :---- | :---- | :---- |
| **Cloud Run** | コンテナ化されたエージェントをデプロイするための柔軟なアプローチ。トラフィックの増減に応じた自動スケーリングと、ゼロへのスケールダウン機能を備え、断続的なワークロードに対して極めて高いコスト効率を発揮する40。 | Identity-Aware Proxy (IAP) をゲートキーパーとして配置し、Web UIからAPIエンドポイントまで、すべてのインバウンドトラフィックを均一に認証および保護する41。 |
| **Vertex AI Agent Engine** | AIエージェントの運用に特化して設計されたオピニオネイテッド（独自の設計思想を持つ）なフルマネージドサービス。Agent Starter Pack等のツールチェーンと密接に統合され、インフラ管理のオーバーヘッドを最小化する6。 | Google CloudのIdentity and Access Management (IAM) と深く統合される。実行主体に roles/iam.serviceAccountUser などの権限を付与し、API呼び出しに対してはOpenID Connect (OIDC) トークンを利用して検証を行う25。 |

特にAPI連携やA2Aプロトコルを利用したプログラム間の非同期通信においては、セキュリティリスクが重大な懸念事項となる41。これらの通信においては、サービスアカウントに紐づいた短命な認証情報や、GoogleのOIDCプロバイダーによって署名されたJSON Web Token (JWT) をAuthorizationヘッダーに含めることで、リクエストの正当性と対象オーディエンス（Audience）が厳格に検証される41。この包括的な認証フローの確立が、エンタープライズレベルでのマルチエージェントシステムの安全な運用を支える基盤となる41。

## **公式リソースおよび関連リンク集**

開発環境のセットアップから高度なアーキテクチャ設計に至るまで、より詳細な情報や実装例を参照するための主要な技術リソースを以下に整理する。これらは公式のドキュメント、オープンソースリポジトリ、および関連する標準化イニシアチブの仕様書を含む。

| カテゴリ | リソース名称およびURL | 概要および内容 |
| :---- | :---- | :---- |
| **公式ドキュメント** | **ADK Official Documentation** https://google.github.io/adk-docs/ | フレームワークの基本概念、各エージェントタイプの詳細、ツールの利用方法、および全体的なアーキテクチャの設計指針を網羅した包括的技術文書11。 |
| **公式ドキュメント** | **Deploying to Vertex AI Agent Engine** https://docs.cloud.google.com/agent-builder/agent-engine/deploy | ADKエージェントを本番環境であるVertex AI Agent Engineへデプロイするための手順、オプション設定、およびIAM権限の構成に関する公式ガイド25。 |
| **公式ドキュメント** | **ADK Evaluation Guide** https://google.github.io/adk-docs/evaluate/ | 軌跡評価と応答評価の概念、テストケース（.test.json）の作成方法、およびCLIを通じた自動評価の実行方法に関する解説36。 |
| **外部ツール連携** | **MCP Tools Integration** https://google.github.io/adk-docs/tools-custom/mcp-tools/ | Model Context Protocolを利用した外部サーバーとの統合、McpToolsetクラスの使用方法、およびGoogle Mapsやファイルシステムへの安全なアクセス例22。 |
| **通信プロトコル** | **Agent2Agent (A2A) Protocol Website** https://a2a-protocol.org/ | Linux Foundationによるオープン標準プロトコルの公式仕様。エージェント間通信のメカニズム、エージェントカードの構造、および関連フレームワークの仕様定義31。 |
| **コードサンプル** | **ADK Samples Repository** https://github.com/google/adk-samples | Python、Go、Java、TypeScriptの各言語で記述された、多岐にわたるドメイン（金融、医療、エンジニアリング等）の実践的なエージェント実装サンプル群3。 |
| **コードサンプル** | **Agent Starter Pack** https://github.com/GoogleCloudPlatform/agent-starter-pack | CI/CDパイプライン、Terraform設定を含む、本番環境レベルのディレクトリ構造を自動生成するスキャフォールディングCLIツールのリポジトリ14。 |
| **コードサンプル** | **Google ADK Workflows** https://github.com/MagnIeeT/google-adk-workflows | 直列実行、並列実行、ディスパッチャーパターン、および自己批評エージェントを含む、複雑な旅行計画システムの高度なオーケストレーション例3。 |

#### **引用文献**

1. 🌟 Google Agent Development Kit (ADK): No-Code vs Code-First Agents, 2月 28, 2026にアクセス、 [https://medium.com/@rohitobrai11/google-agent-development-kit-adk-no-code-vs-code-first-agents-28ccc3f44bbb](https://medium.com/@rohitobrai11/google-agent-development-kit-adk-no-code-vs-code-first-agents-28ccc3f44bbb)  
2. Agent Development Kit (ADK), 2月 28, 2026にアクセス、 [https://medium.com/google-cloud/agent-development-kit-adk-c1211cf1c381](https://medium.com/google-cloud/agent-development-kit-adk-c1211cf1c381)  
3. Build multi-agentic systems using Google ADK | Google Cloud Blog, 2月 28, 2026にアクセス、 [https://cloud.google.com/blog/products/ai-machine-learning/build-multi-agentic-systems-using-google-adk](https://cloud.google.com/blog/products/ai-machine-learning/build-multi-agentic-systems-using-google-adk)  
4. Architecting multi-agent systems, 2月 28, 2026にアクセス、 [https://www.youtube.com/watch?v=j\_l-9uNX2SA](https://www.youtube.com/watch?v=j_l-9uNX2SA)  
5. Agent Development Kit: Making it easy to build multi-agent applications, 2月 28, 2026にアクセス、 [https://developers.googleblog.com/en/agent-development-kit-easy-to-build-multi-agent-applications/](https://developers.googleblog.com/en/agent-development-kit-easy-to-build-multi-agent-applications/)  
6. Build and manage multi-system agents with Vertex AI | Google Cloud Blog, 2月 28, 2026にアクセス、 [https://cloud.google.com/blog/products/ai-machine-learning/build-and-manage-multi-system-agents-with-vertex-ai](https://cloud.google.com/blog/products/ai-machine-learning/build-and-manage-multi-system-agents-with-vertex-ai)  
7. google/adk-python: An open-source, code-first Python toolkit for building, evaluating, and deploying sophisticated AI agents with flexibility and control. \- GitHub, 2月 28, 2026にアクセス、 [https://github.com/google/adk-python](https://github.com/google/adk-python)  
8. Overview of Agent Development Kit | Vertex AI Agent Builder \- Google Cloud Documentation, 2月 28, 2026にアクセス、 [https://docs.cloud.google.com/agent-builder/agent-development-kit/overview](https://docs.cloud.google.com/agent-builder/agent-development-kit/overview)  
9. Building Collaborative AI Agent Ecosystems: A Deep Dive into ADK, MCP & A2A with Pokemon, 2月 28, 2026にアクセス、 [https://medium.com/google-cloud/building-collaborative-ai-agent-ecosystems-a-deep-dive-into-adk-mcp-a2a-with-pokemon-5c877d5653e7](https://medium.com/google-cloud/building-collaborative-ai-agent-ecosystems-a-deep-dive-into-adk-mcp-a2a-with-pokemon-5c877d5653e7)  
10. Build Multi-Agent Systems with ADK \- Google Codelabs, 2月 28, 2026にアクセス、 [https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/3-developing-agents/build-a-multi-agent-system-with-adk](https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/3-developing-agents/build-a-multi-agent-system-with-adk)  
11. Index \- Agent Development Kit (ADK) \- Google, 2月 28, 2026にアクセス、 [https://google.github.io/adk-docs/](https://google.github.io/adk-docs/)  
12. Multi-Agent Example using Google's Agent Development Kit (ADK) \- Medium, 2月 28, 2026にアクセス、 [https://medium.com/@imranburki.ib/multi-agent-example-using-googles-agent-development-kit-adk-500312361ebb](https://medium.com/@imranburki.ib/multi-agent-example-using-googles-agent-development-kit-adk-500312361ebb)  
13. Developer's guide to multi-agent patterns in ADK, 2月 28, 2026にアクセス、 [https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)  
14. GoogleCloudPlatform/agent-starter-pack: Ship AI Agents to Google Cloud in minutes, not months. Production-ready templates with built-in CI/CD, evaluation, and observability. \- GitHub, 2月 28, 2026にアクセス、 [https://github.com/GoogleCloudPlatform/agent-starter-pack](https://github.com/GoogleCloudPlatform/agent-starter-pack)  
15. How to Build Your First Google A2A Project: A Step-by-Step Tutorial | Trickle blog, 2月 28, 2026にアクセス、 [https://trickle.so/blog/how-to-build-google-a2a-project](https://trickle.so/blog/how-to-build-google-a2a-project)  
16. Building AI Agents with ADK: The Foundation \- Google Codelabs, 2月 28, 2026にアクセス、 [https://codelabs.developers.google.com/devsite/codelabs/build-agents-with-adk-foundation](https://codelabs.developers.google.com/devsite/codelabs/build-agents-with-adk-foundation)  
17. How to Build AI Agents From Scratch (Full Step-By-Step Guide Using Python), 2月 28, 2026にアクセス、 [https://medium.com/@proflead/how-to-build-ai-agents-from-scratch-full-step-by-step-guide-using-python-1fd4b096a577](https://medium.com/@proflead/how-to-build-ai-agents-from-scratch-full-step-by-step-guide-using-python-1fd4b096a577)  
18. Google Cloud COE Multi AI Agent using ADK (Agent Development Kit) built in 26 mintues, 2月 28, 2026にアクセス、 [https://www.youtube.com/watch?v=W1SY8XbucQc](https://www.youtube.com/watch?v=W1SY8XbucQc)  
19. Multi-tool agent \- Agent Development Kit (ADK) \- Google, 2月 28, 2026にアクセス、 [https://google.github.io/adk-docs/get-started/quickstart/](https://google.github.io/adk-docs/get-started/quickstart/)  
20. Quickstart: Exposing a remote agent via A2A \- Google, 2月 28, 2026にアクセス、 [https://google.github.io/adk-docs/a2a/quickstart-exposing/](https://google.github.io/adk-docs/a2a/quickstart-exposing/)  
21. Quickstart: Develop and deploy agents on Vertex AI Agent Engine with Agent Development Kit | Vertex AI Agent Builder | Google Cloud Documentation, 2月 28, 2026にアクセス、 [https://docs.cloud.google.com/agent-builder/agent-engine/quickstart-adk](https://docs.cloud.google.com/agent-builder/agent-engine/quickstart-adk)  
22. MCP tools \- Agent Development Kit (ADK) \- Google, 2月 28, 2026にアクセス、 [https://google.github.io/adk-docs/tools-custom/mcp-tools/](https://google.github.io/adk-docs/tools-custom/mcp-tools/)  
23. AI Agent Engineering in Go with the Google ADK | by Karl Weinmeister | Google Cloud \- Community | Jan, 2026, 2月 28, 2026にアクセス、 [https://medium.com/google-cloud/ai-agent-engineering-in-go-with-the-google-adk-4f2a992c6db4](https://medium.com/google-cloud/ai-agent-engineering-in-go-with-the-google-adk-4f2a992c6db4)  
24. Deploy to Vertex AI Agent Engine \- Agent Development Kit (ADK), 2月 28, 2026にアクセス、 [https://google.github.io/adk-docs/deploy/agent-engine/](https://google.github.io/adk-docs/deploy/agent-engine/)  
25. Deploy an agent | Vertex AI Agent Builder \- Google Cloud Documentation, 2月 28, 2026にアクセス、 [https://docs.cloud.google.com/agent-builder/agent-engine/deploy](https://docs.cloud.google.com/agent-builder/agent-engine/deploy)  
26. Building secure, real time AI agents with Google ADK & MCP Toolbox, 2月 28, 2026にアクセス、 [https://www.youtube.com/watch?v=6NXDc4cPNG8](https://www.youtube.com/watch?v=6NXDc4cPNG8)  
27. Connecting ADK Agents to MCP Servers \- YouTube, 2月 28, 2026にアクセス、 [https://www.youtube.com/watch?v=JnKkdHaatwU](https://www.youtube.com/watch?v=JnKkdHaatwU)  
28. ADK meets MCP: Bridging Worlds of AI Agents | by Kaz Sato | Google Cloud \- Medium, 2月 28, 2026にアクセス、 [https://medium.com/google-cloud/adk-meets-mcp-bridging-worlds-of-ai-agents-1ed96ef5399c](https://medium.com/google-cloud/adk-meets-mcp-bridging-worlds-of-ai-agents-1ed96ef5399c)  
29. Use Google ADK and MCP with an external server | Google Cloud Blog, 2月 28, 2026にアクセス、 [https://cloud.google.com/blog/topics/developers-practitioners/use-google-adk-and-mcp-with-an-external-server](https://cloud.google.com/blog/topics/developers-practitioners/use-google-adk-and-mcp-with-an-external-server)  
30. Getting Started with Agent2Agent (A2A) Protocol: A Purchasing Concierge and Remote Seller Agent Interactions on Cloud Run and Agent Engine | Google Codelabs, 2月 28, 2026にアクセス、 [https://codelabs.developers.google.com/intro-a2a-purchasing-concierge](https://codelabs.developers.google.com/intro-a2a-purchasing-concierge)  
31. Agent2Agent (A2A) is an open protocol enabling communication and interoperability between opaque agentic applications. \- GitHub, 2月 28, 2026にアクセス、 [https://github.com/a2aproject/A2A](https://github.com/a2aproject/A2A)  
32. A2A Explained with Google ADK. You’ve probably heard about AI agents…, 2月 28, 2026にアクセス、 [https://michael-scherding.medium.com/a2a-explained-with-google-adk-140b35ad04ad](https://michael-scherding.medium.com/a2a-explained-with-google-adk-140b35ad04ad)  
33. Announcing the Agent2Agent Protocol (A2A) \- Google for Developers Blog, 2月 28, 2026にアクセス、 [https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)  
34. ADK with Agent2Agent (A2A) Protocol \- Agent Development Kit (ADK), 2月 28, 2026にアクセス、 [https://google.github.io/adk-docs/a2a/](https://google.github.io/adk-docs/a2a/)  
35. a2aproject/a2a-samples: Samples using the Agent2Agent (A2A) Protocol \- GitHub, 2月 28, 2026にアクセス、 [https://github.com/a2aproject/a2a-samples](https://github.com/a2aproject/a2a-samples)  
36. Why Evaluate Agents \- Agent Development Kit (ADK) \- Google, 2月 28, 2026にアクセス、 [https://google.github.io/adk-docs/evaluate/](https://google.github.io/adk-docs/evaluate/)  
37. Evaluating Agents with ADK \- Google Codelabs, 2月 28, 2026にアクセス、 [https://codelabs.developers.google.com/adk-eval/instructions](https://codelabs.developers.google.com/adk-eval/instructions)  
38. google-adk-tutorial/12\_evaluation.md at main \- GitHub, 2月 28, 2026にアクセス、 [https://github.com/Kjdragan/google-adk-tutorial/blob/main/12\_evaluation.md](https://github.com/Kjdragan/google-adk-tutorial/blob/main/12_evaluation.md)  
39. Agent Factory Recap: A Deep Dive into Agent Evaluation, Practical Tooling, and Multi-Agent Systems | Google Cloud Blog, 2月 28, 2026にアクセス、 [https://cloud.google.com/blog/topics/developers-practitioners/agent-factory-recap-a-deep-dive-into-agent-evaluation-practical-tooling-and-multi-agent-systems](https://cloud.google.com/blog/topics/developers-practitioners/agent-factory-recap-a-deep-dive-into-agent-evaluation-practical-tooling-and-multi-agent-systems)  
40. What are AI agents? Definition, examples, and types | Google Cloud, 2月 28, 2026にアクセス、 [https://cloud.google.com/discover/what-are-ai-agents](https://cloud.google.com/discover/what-are-ai-agents)  
41. Deploying AI Agents in the Enterprise without Losing your Humanity using ADK and Google Cloud \- Médéric Hurier (Fmind), 2月 28, 2026にアクセス、 [https://fmind.medium.com/deploying-ai-agents-in-the-enterprise-using-adk-and-google-cloud-b49e7eda3b41](https://fmind.medium.com/deploying-ai-agents-in-the-enterprise-using-adk-and-google-cloud-b49e7eda3b41)  
42. Roles for service account authentication | Identity and Access Management (IAM), 2月 28, 2026にアクセス、 [https://docs.cloud.google.com/iam/docs/service-account-permissions](https://docs.cloud.google.com/iam/docs/service-account-permissions)  
43. Service accounts overview | Identity and Access Management (IAM) | Google Cloud Documentation, 2月 28, 2026にアクセス、 [https://docs.cloud.google.com/iam/docs/service-account-overview](https://docs.cloud.google.com/iam/docs/service-account-overview)  
44. A collection of sample agents built with Agent Development Kit (ADK) \- GitHub, 2月 28, 2026にアクセス、 [https://github.com/google/adk-samples](https://github.com/google/adk-samples)