import openai
openai.api_key = '...'


def prompt(question):
    completion = openai.chat.completions.create(
    model = 'gpt-3.5-turbo',
    messages = [
    {'role': 'user', 'content': question}
    ],
    temperature = 0  
    )
    answer =  completion['choices'][0]['message']['content']
    return answer

question = "Hello my friend"
print(prompt(question))