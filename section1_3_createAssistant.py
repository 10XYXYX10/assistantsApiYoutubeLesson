#■[ ライブラリ「openai 」をインストール ]
#pip install openai 


#■[ 各種ライブラリをインポート ]
import os
from openai import OpenAI
import time


#■[ openai インスタンスを生成 ]
os.environ["OPENAI_API_KEY"] = "secretKey"
client = OpenAI()


#■[ Assistantの振る舞いを決めるプロンプト ]
instructions="あなたが持っている情報を元に、ユーザーの質問に対して100字以内で、迅速に答えて下さい。"


#■[ Assistantの作成 ]
my_assistant = client.beta.assistants.create(
    name="Test Assistant", #任意の名前
    instructions=instructions,#Assistantの振る舞いを決めるプロンプト
    model="gpt-4o-mini",  # モデルを選択
)
assistant_id = my_assistant.id
print(assistant_id)


#■[ Threadの作成 ]
empty_thread = client.beta.threads.create()
thread_id = empty_thread.id
print(thread_id)


#■[ Messageの作成 ]
createMessageResult = client.beta.threads.messages.create(
    thread_id=thread_id,
    role="user",
    content="EVシフトは、地球温暖化の対策として有効ですか？？",
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
#・status = 'queued' | 'in_progress' | 'requires_action' | 'cancelling' | 'cancelled' | 'failed' | 'completed' | 'incomplete' | 'expired'
run_retrieve = client.beta.threads.runs.retrieve(
  thread_id=thread_id,
  run_id=run_id,
)
print(run_retrieve.status)


#■[ 処理が完了するまで待機 ]
for i in range(51):
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