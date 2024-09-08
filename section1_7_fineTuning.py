#◆【参考URL】
#■https://community.openai.com/t/api-error-code-500-fine-tuned-model/791933/7
#　https://github.com/openai/openai-python/discussions/742
#　https://hackmd.io/@toshiole/rksFkv0JA



#■[ 各種ライブラリをインポート ]
import os
from openai import OpenAI
import time
import json



#■[ openai インスタンスを生成 ]
#os.environ["OPENAI_API_KEY"] = "-secretKey-"
client = OpenAI()



#■[ FineTuningで使用する教師データ ]
jsonl_file_path = "./go_info.jsonl"





#■[ ファイルのチェック ]＊ℓ29～ℓ155 までを1つのセルに入力して下さい
import tiktoken
import numpy as np
from collections import defaultdict

#「with open(jsonl_file_path) as f:」←文字コードが原因のエラーになるため以下に修正
with open(jsonl_file_path, 'r', encoding='utf-8') as f:
    dataset = [json.loads(line) for line in f]

print("Num examples:", len(dataset))
print("First example:")
for message in dataset[0]["messages"]:
    print(message)

format_errors = defaultdict(int)

for ex in dataset:
    if not isinstance(ex, dict):
        format_errors["data_type"] += 1
        continue

    messages = ex.get("messages", None)
    if not messages:
        format_errors["missing_messages_list"] += 1
        continue

    for message in messages:
        if "role" not in message or "content" not in message:
            format_errors["message_missing_key"] += 1

        if any(k not in ("role", "content", "name") for k in message):
            format_errors["message_unrecognized_key"] += 1

        if message.get("role", None) not in ("system", "user", "assistant"):
            format_errors["unrecognized_role"] += 1

        content = message.get("content", None)
        if not content or not isinstance(content, str):
            format_errors["missing_content"] += 1

    if not any(message.get("role", None) == "assistant" for message in messages):
        format_errors["example_missing_assistant_message"] += 1

if format_errors:
    print("Found errors:")
    for k, v in format_errors.items():
        print(f"{k}: {v}")
else:
    print("No errors found")
# Beyond the structure of the message, we also need to ensure that the length does not exceed the 4096 token limit.

# Token counting functions
encoding = tiktoken.get_encoding("cl100k_base")

# not exact!
# simplified from https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
def num_tokens_from_messages(messages, tokens_per_message=3, tokens_per_name=1):
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3
    return num_tokens

def num_assistant_tokens_from_messages(messages):
    num_tokens = 0
    for message in messages:
        if message["role"] == "assistant":
            num_tokens += len(encoding.encode(message["content"]))
    return num_tokens

def print_distribution(values, name):
    print(f"\n#### Distribution of {name}:")
    print(f"min / max: {min(values)}, {max(values)}")
    print(f"mean / median: {np.mean(values)}, {np.median(values)}")
    print(f"p5 / p95: {np.quantile(values, 0.1)}, {np.quantile(values, 0.9)}")
# Last, we can look at the results of the different formatting operations before proceeding with creating a fine-tuning job:

# Warnings and tokens counts
n_missing_system = 0
n_missing_user = 0
n_messages = []
convo_lens = []
assistant_message_lens = []

for ex in dataset:
    messages = ex["messages"]
    if not any(message["role"] == "system" for message in messages):
        n_missing_system += 1
    if not any(message["role"] == "user" for message in messages):
        n_missing_user += 1
    n_messages.append(len(messages))
    convo_lens.append(num_tokens_from_messages(messages))
    assistant_message_lens.append(num_assistant_tokens_from_messages(messages))

print("Num examples missing system message:", n_missing_system)
print("Num examples missing user message:", n_missing_user)
print_distribution(n_messages, "num_messages_per_example")
print_distribution(convo_lens, "num_total_tokens_per_example")
print_distribution(assistant_message_lens, "num_assistant_tokens_per_example")
n_too_long = sum(l > 4096 for l in convo_lens)
print(f"\n{n_too_long} examples may be over the 4096 token limit, they will be truncated during fine-tuning")

# Pricing and default n_epochs estimate
MAX_TOKENS_PER_EXAMPLE = 4096

MIN_TARGET_EXAMPLES = 100
MAX_TARGET_EXAMPLES = 25000
TARGET_EPOCHS = 3
MIN_EPOCHS = 1
MAX_EPOCHS = 25

n_epochs = TARGET_EPOCHS
n_train_examples = len(dataset)
if n_train_examples * TARGET_EPOCHS < MIN_TARGET_EXAMPLES:
    n_epochs = min(MAX_EPOCHS, MIN_TARGET_EXAMPLES // n_train_examples)
elif n_train_examples * TARGET_EPOCHS > MAX_TARGET_EXAMPLES:
    n_epochs = max(MIN_EPOCHS, MAX_TARGET_EXAMPLES // n_train_examples)

n_billing_tokens_in_dataset = sum(min(MAX_TOKENS_PER_EXAMPLE, length) for length in convo_lens)
print(f"Dataset has ~{n_billing_tokens_in_dataset} tokens that will be charged for during training")
print(f"By default, you'll train for {n_epochs} epochs on this dataset")
print(f"By default, you'll be charged for ~{n_epochs * n_billing_tokens_in_dataset} tokens")
print("See pricing page to estimate total costs")





#■[ ファインチューニングの実行 ]
res = client.fine_tuning.jobs.create(
  training_file=file_id,
  model="gpt-3.5-turbo"
)
ft_id = res.id
print(res)
print('-----')
print(res.id)



#■[ 実行中のファインチューニングのステータスを確認 ]
#status: 'validating_files' | 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled';
for i in range(100):
    res = client.fine_tuning.jobs.retrieve(ft_id)
    status = res.status
    print(status)
    
    if status == 'succeeded':
        break
    elif status == 'failed' or status == 'cancelled':
        raise Exception("The fine-tuning process has failed or was cancelled.")  # エラーを投げる
        break
    time.sleep(10)



#■[ ファインチューニングジョブの詳細を取得 ]
#・ファインチューニングのジョブとは、特定のデータセットを使用して既存のモデルをさらにトレーニングするプロセスのこと
fine_tuning_job = client.fine_tuning.jobs.retrieve(ft_id)
print(fine_tuning_job)



#■[ モデルの名前を取得 ]
model_name = fine_tuning_job.fine_tuned_model
print(model_name)



#■[ Fine-tunedモデルを使用＆実行 ]
completion = client.chat.completions.create(
    model=model_name,
    messages=[
        {
            "role": "user",
            "content": "Go言語の並行処理について説明してください",
        },
    ],
)
print(completion)



#■[ content箇所のみ抽出 ]
print(completion.choices[0].message.content)



##############################
##############################
#◆【後片付け】
#■[ ファイルの削除 ]
res =  client.files.delete(file_id)
print(res)