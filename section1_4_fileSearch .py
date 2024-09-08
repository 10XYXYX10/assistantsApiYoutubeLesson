#■[ 各種ライブラリをインポート ]
import os
from openai import OpenAI
import time


#■[ openai インスタンスを生成 ]
os.environ["OPENAI_API_KEY"] = "secretKey"
client = OpenAI()


#■[ Fileのアップロード ]
#・playgroundのstorageでアップロードファイルを確認できる
uploaded_file = client.files.create(
  file=open("./fileSearch.txt", "rb"),
  purpose="assistants",
)
file_id = uploaded_file.id
print(file_id)


#■[VectorStore作成]
#・VectorStoreという空間を作って、そこにアップロードしたファイルを紐づけ。
#　そして、そのVectorStoreをAssistant作成時にAssistantに紐づけ。
#　こうすることで、アップロードしたファイルの内容を元に回答を生成することが可能に
vectorStore = client.beta.vector_stores.create(
    name='testVectorStore',
    file_ids=[file_id],
    chunking_strategy={
        #大きなファイルを効率的に扱うために、ファイルを小さなチャンク(データブロック)に分割。
        #autoは、システムが最適な方法で自動的にチャンク化を実行してくれる
        "type": "auto"
    },
    expires_after={
        #有効期限を、最後に使用された日から1日経過したら削除、するように設定
        "anchor": "last_active_at",#last_active_at = 最後に使用された日
        "days": 1 # 1日
    },
)
vectorStoreId = vectorStore.id
print(vectorStore)
print('----')
print(vectorStore.id)


#■[ Assistantの振る舞いを決めるプロンプト ]
instructions="ユーザーの質問に対して、tool_resourcesで関連付けられたファイルの内容を元に、回答を生成して下さい。"


#■[ Assistantの作成 ]
#・openai platformのページでこのコードで作成されたAssistantを確認可能
my_assistant = client.beta.assistants.create(
    name="Test Assistant For File Search",#任意の名前
    instructions=instructions,#Assistantの振る舞いを決めるプロンプト
    model="gpt-4o-mini",  # Assitantが使用するモデルを選択
    tools=[{"type":"file_search"}],  # File Searchを有効化
    tool_resources={ # File Searchの際の参照元を指定
        "file_search":{
            "vector_store_ids":[vectorStoreId]
        }
    }
)
assistant_id = my_assistant.id
print(assistant_id)


#■[ Threadの作成 ]
#・openai platformのページでこのコードで作成されたThreadを確認可能
empty_thread = client.beta.threads.create()
thread_id = empty_thread.id
print(thread_id)


#■[ Messageの作成 ]
createMessageResult = client.beta.threads.messages.create(
    thread_id=thread_id,
    role="user",
    content="呪術廻戦に登場するキャラクターの強さのランキングをトップ3まで教えて？",
)
message_id = createMessageResult.id
print(createMessageResult)
print('-----')
print(message_id)


#■[ Assistantの実行 ]
run = client.beta.threads.runs.create(
  thread_id=thread_id,
  assistant_id=assistant_id,
)
run_id = run.id
print(run_id)


#■[ Runのステータスの確認 ]
#・'queued' | 'in_progress' | 'requires_action' | 'cancelling' | 'cancelled' | 'failed' | 'completed' | 'incomplete' | 'expired'
run_retrieve = client.beta.threads.runs.retrieve(
  thread_id=thread_id,
  run_id=run_id,
)
print(run_retrieve.status)


#■[ 処理が完了するまで待機 ]
for i in range(50):
    print(f'={i+1}回目=')
    run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
    status = run.status
    if status == 'requires_action' or status == 'completed':
        break
    elif status in ['failed', 'cancelling', 'cancelled', 'incomplete', 'expired']:
        raise Exception(f"Run failed with status: {status}")  # エラーを投げる
    time.sleep(5)
    
runStatus = run.status
print(runStatus)


#■[ 特定のthread内の 全messageを取得 ]
messages = client.beta.threads.messages.list(
  thread_id=thread_id
)
print(messages.data)


#■[ ループでmessageを1つづつ確認 ]
for message in messages.data:
  print(message.content[0].text.value)
  print('-----')


#■[ Threadの削除 ]
res = client.beta.threads.delete(thread_id)
print(res)


#■[ Assistantの削除 ]
res = client.beta.assistants.delete(assistant_id)
print(res)


#■[ ファイルの削除 ]
res =  client.files.delete(file_id)
print(res)