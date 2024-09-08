#■[ 各種ライブラリをインポート ]
import os
import requests
from openai import OpenAI
from openai.types.chat import ChatCompletionToolParam
from typing import Union
import time
import json



#■[ openai インスタンスを生成 ]
os.environ["OPENAI_API_KEY"] = "-secretKey-"
client = OpenAI()



#■[ Assistantに組み込む関数 ]
#・処理で外部のAPIを利用しているこの関数を、Assistant生成時に組み込む。
#　こうすることで、ユーザーからの要求に応じて、AIが自律的にこの関数を用いるべきか判断。
#　必要と判断したらば、この関数を実行して、情報を引き出した上で回答を生成してくれる
def get_eth_btc_rate(currency: str) -> Union[str, float]:
    if currency=='イーサリアム' or currency=='ethreum' or currency=='eth' or currency=='Ethereum':
        url = 'https://api.excelapi.org/crypto/rate?pair=eth-jpy'
        response = requests.get(url, headers={'Cache-Control': 'no-store'})
        data = response.json()
        return float(data)
    elif currency=='ビットコイン' or currency=='btc' or currency=='Btc' or currency=='Bitcoin':
        url = 'https://api.excelapi.org/crypto/rate?pair=btc-jpy'
        response = requests.get(url, headers={'Cache-Control': 'no-store'})
        data = response.json()
        return float(data)
    else :
        return 'EthreumとBitcoin以外のレートは分かりません'

#■[ 関数名と関数をマッピングする辞書 ]
#・Assistantは、実行すべき関数を文字列で指示してくる
function_map = {
    "get_eth_btc_rate": get_eth_btc_rate,
}

#■[ 使用例 ]
rate = get_eth_btc_rate('btc')
print(f"rate: {rate}")



#■[ Assistantの作成時に、パラメータのtoolsに渡す値を定義 ]
tools = [
    #パラメータtoolsを定義するためのクラス。先頭のライブラリのブロックでインポート済み。
    ChatCompletionToolParam({
        #Function Calling を用いる場合は、文字列で"function"と指定する
        "type": "function",
        #呼び出すFunctionの詳細
        "function": {
            #呼び出す関数名
            "name": "get_eth_btc_rate", 
            #関数についての解説。Assistantが関数を呼び出すか否かの判断材料となる
            "description": "EthreumまたはBitCoinの現在レートを取得する", 
            #関数実行時のパラメータについて定義するブロック
            "parameters": {
                #今回は、パラメータの詳細をObject形式で設定しているので文字列で"object"
                "type": "object",
                #関数に渡すプロパティを定義。
                "properties": {
                    #プロパティ名は"currency"。
                    "currency": {
                        #型はString
                        "type": "string",
                        #プロパティcurrencyにどの様な値を渡すべきか、Assistantに説明。
                        "description": "仮想通貨のイーサリアムを示す単語(例：eth,ethreum,イーサリアム) or ビットコインを示す単語(例：ビットコイン,Btc,btc)",
                    },
                },
                #currencyを必須パラメータとして指定
                "required": ["currency"],
            },
        },
    }),
]



#■[ Assistantの振る舞いを決めるプロンプト ]
instructions="""
仮想通貨のEthreumまたはBitCoinのレートを聞かれた際は、与えられた関数「get_eth_btc_rate」を使って質問に答えてください。
それ以外の質問に関しては、貴方の持つ情報を元に回答して下さい。
"""



#■[ Assistantの作成 ]
my_assistant = client.beta.assistants.create(
    name='Test_Function Calling',
    instructions=instructions,
    model="gpt-4o-mini", 
    tools=tools,
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
    content="BitcoinとEthreumの現在レートを教えて",
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



#■[ 呼び出すべき関数の情報を取得 ]
tool_calls = run.required_action.submit_tool_outputs.tool_calls
print(tool_calls)
print('---')
print(tool_calls[0].function)
print(tool_calls[0].function.name)#実行すべき関数目
print(tool_calls[0].function.arguments)#関数に渡すパラメーター情報



# ■[ 関数に渡す引数の調整 ]
arguments = json.loads(tool_calls[0].function.arguments)
dictValues = arguments.values()
listValues = list(dictValues)
print(dictValues)
print(listValues)
print(*listValues)



#■[ requires_action状態のAssistantに渡す、関数の実行結果のデータを定義 ]
tool_outputs = [] #関数の実行結果のデータを追加していく
for tool_call in tool_calls:
    fncName = tool_call.function.name #実行すべき関数名
    targetFnc = function_map[fncName] # 序盤に定義した辞書型のfunction_mapを用いて、文字列の関数名から、実行すべき関数を取得
    
    arguments = json.loads(tool_call.function.arguments)# JSONを辞書型に：「'{"currency": "Bitcoin"}'」→「{'currency': 'Bitcoin'}」
    dictValues = arguments.values()# value値のみを抽出：dict_values(['Bitcoin'])
    listValues = list(dictValues) # list形式に：['Bitcoin']
    result = targetFnc(*listValues)# listを展開し引数として渡して関数を実行
    
    tool_outputs.append({
        "tool_call_id": tool_call.id,#Assistantに呼び出すよう指示されたtoolのid
        "output": f"実行結果：{result}",#関数の実行結果を文字列で整形
    })
print(tool_outputs)



#■[ Assistantに、関数の実行結果が格納された変数「tool_outputs」を渡して、再度実行 ]
try:
    run = client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread_id,
        run_id=run_id,
        tool_outputs=tool_outputs
    )
    run_id = run.id
    print(run_id)
except Exception as e:
    errData = e
    #「'Runs in status "expired」は時間切れを意味します。messageの作成からやり直して下さい。
    print(f"予期せぬエラーが発生しました: {str(e)}") 



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



##############################
##############################
#◆【BrushUp】
content1='プログラミングのgo言語についての解説を、100字以内でお願いします！'
content2='BitcoinとEthreumの現在レートを教えて'



#■[ Messageの作成 ]
createMessageResult = client.beta.threads.messages.create(
    thread_id=thread_id,
    role="user",
    content=content1,
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



#■[ runStatusの値に応じて処理を分岐 ]
if runStatus == 'requires_action':
    # 呼び出すべき関数情報
    tool_calls = run.required_action.submit_tool_outputs.tool_calls
    #ループ処理でAssistantに渡す関数の実行結果の情報を整理
    tool_outputs = []
    for tool_call in tool_calls:
        fncName = tool_call.function.name
        targetFnc = function_map[fncName]
        arguments = json.loads(tool_call.function.arguments)
        dictValues = arguments.values()
        listValues = list(dictValues)
        result = targetFnc(*listValues)
        tool_outputs.append({
            "tool_call_id": tool_call.id,
            "output": f"実行結果：{result}",
        })
        
    #この関数は、ツールの実行結果をAssistantに送信するために使用されます。
    #Assistantが特定のツールの使用を要求した後、その結果をこの関数を通じて提供します。
    run = client.beta.threads.runs.submit_tool_outputs(
      thread_id=thread_id,
      run_id=run_id,
      tool_outputs=tool_outputs
    )
    run_id = run.id
    
    # Runが completed になるまで繰り返す
    for i in range(100):
        print(f'={i+1}回目=')
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run.status == 'completed':
            print(run.status)
            break
        elif status in ['failed', 'cancelling', 'cancelled', 'incomplete', 'expired']:
            raise Exception(f"Run failed with status: {status}")  # エラーを投げる
        else:
            time.sleep(3)
    runStatus = run.status



if runStatus == 'completed':
    #特定のthread内の 全messageを取得
    messages = client.beta.threads.messages.list(
      thread_id=thread_id
    )
    
    #■[ ループでmessageを1つづつ確認 ]
    for message in messages.data:
      print(message.content[0].text.value)
      print('-----')
else:
    print(runStatus)



##############################
##############################
#◆【後片付け】

#■[ Threadの削除 ]
res = client.beta.threads.delete(thread_id)
print(res)

#■[ Assistantの削除 ]
res = client.beta.assistants.delete(assistant_id)
print(res)