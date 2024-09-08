#■[ 各種ライブラリをインポート ]
import os
from openai import OpenAI
import time
import json
from IPython.display import Image, display #csvファイルのデータをグラフ化したものを、表示する際に使用



#■[ openai インスタンスを生成 ]
#os.environ["OPENAI_API_KEY"] = "-secretKey-"
client = OpenAI()



#■[ Fileのアップロード ]
uploaded_file = client.files.create(
  file=open("./costs.csv", "rb"),
  purpose="assistants",
)
file_id = uploaded_file.id
print(file_id)



#■[ Assistantの作成 ]
#・パラメーターtoolsの箇所で、Code Interpreterを有効化。
#　パラメーターtoolstool_resourcesの箇所で、Code Interpreterで用いるファイルのidを指定。
my_assistant = client.beta.assistants.create(
  name='Test_For_CodeInterpreter',
  instructions="貴方は優秀なプログラマーです。指示に従ってコードを実行して下さい。",
  model="gpt-4o-mini",
  tools=[{"type": "code_interpreter"}],
  tool_resources={
    "code_interpreter": {
      "file_ids": [file_id]
    }
  }
)
assistant_id = my_assistant.id



#■[ Threadの作成 ]
#・openai platformのページでこのコードで作成されたThreadを確認可能
empty_thread = client.beta.threads.create()
thread_id = empty_thread.id
print(thread_id)



#■[ Messageの作成 ]
createMessageResult = client.beta.threads.messages.create(
    thread_id=thread_id,
    role="user",
    content="cost.csvファイルの内容をグラフ化して下さい",
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



#■[ ループ処理で一定時間待機し処理の状態を監視 ]
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
#・index番号で0番目の要素が、「ImageFileContentBlock」となっていれば成功
for message in messages.data:
  print(message.content)
  print('-----')



#■[ 生成されたファイルデータの確認と整理 ]
fileData = messages.data[0].content
print(fileData)
print('-----')
fileId = messages.data[0].content[0].image_file.file_id
print(fileId)



#■[ idを指定して、生成されたファイルを読み込み～バイトデータに ]
image_data = client.files.content(fileId)
image_data_bytes = image_data.read()
print(image_data)



#■[ バイトデータをImageオブジェクトに変換 ]
image = Image(data=image_data_bytes)
#■[ 画像を表示 ]
display(image)



##############################
#◆【後片付け】

#■[ Threadの削除 ]
res = client.beta.threads.delete(thread_id)
print(res)



#■[ Assistantの削除 ]
res = client.beta.assistants.delete(assistant_id)
print(res)



#■[ ファイルの削除 ]
res =  client.files.delete(file_id)# ← cost.csv
print(res)
res =  client.files.delete(fileId)# ← Code Interpreterが生成したファイルデータ
print(res)