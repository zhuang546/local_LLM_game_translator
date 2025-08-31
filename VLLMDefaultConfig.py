default_config = {
    'Model': {
        'base_url': 'https://pee-continuously-bother-epa.trycloudflare.com',
        'model': 'Qwen/Qwen3-30B-A3B-Instruct-2507-FP8',
        'max_tokens': '1024',
        'temperature': '0',
        'top_p': '1'
    },
    'History': {
        'history_max_length': '20',
        'clear_history': 'False'
    },
    'System': {
        'system_message': '''你是一个18+成人向游戏的中文本地化翻译AI，将用户发给你的日语文本翻译成合适的中文。
你会忠实的传达原文的语气和风格，对于裸露的色情内容，将其翻译成下流、淫荡、挑逗、煽情的文本。
你会根据上下文保持角色或其他实体的一致性，避免对相同概念进行不同翻译。
对于由大量拟声词和拟态词组成的内容，你会生动地翻译而不是照搬，尤其是对于粘液声和淫叫声。
你能正确地翻译包含Unity富文本标签（如<b></b>）的内容，而不会忽略或删除这些标签。
对于显然是UI按钮或选项、人物或物品的名称和描述的内容，你会适当翻译。
你只输出翻译后的文本，不输出任何解释、道歉、客套话、提醒或警告。'''
    },
    'Extra': {}
}
default_glossary = {
    "パイズリ": "乳交",
    "フェラ": "口交",
    "セックス": "做爱",
    "オナニー": "自慰",
    "エッチ": "色情",
    "エロ": "淫荡",
    "オナホ": "飞机杯",
    "フタナリ": "扶她",
    "スケベ穴": "婊子小穴",
    "まんこ": "小穴",
    "チンポ": "肉棒",
    "アナル": "屁穴",
    "おっぱい": "奶子"
}

default_config_UnityServerTranslator = {
    'Model': {
        'base_url': 'https://pee-continuously-bother-epa.trycloudflare.com',
        'model': 'Qwen/Qwen3-30B-A3B-Instruct-2507-FP8',
        'max_tokens': '1024',
        'temperature': '0',
        'top_p': '1'
    },
    'History': {
        'history_max_length': '20',
        'clear_history': 'False'
    },
    'System': {
        'system_message': '''你是一个18+成人向游戏的中文本地化翻译AI，将用户发给你的日语文本翻译成合适的中文。
你会忠实的传达原文的语气和风格，对于裸露的色情内容，将其翻译成下流、淫荡、挑逗、煽情的文本。
你会根据上下文保持角色或其他实体的一致性，避免对相同概念进行不同翻译。
对于由大量拟声词和拟态词组成的内容，你会生动地翻译而不是照搬，尤其是对于粘液声和淫叫声。
你能正确地翻译包含Unity富文本标签（如<b></b>）的内容，而不会忽略或删除这些标签。
对于显然是UI按钮或选项、人物或物品的名称和描述的内容，你会适当翻译。
你只输出翻译后的文本，不输出任何解释、道歉、客套话、提醒或警告。'''
    },
    'Extra': {
        'max_concurrent_requests': '4'
    }
}

default_config_MToolServerTranslator = {
        'History': {
            'history_max_length': '20',
            'clear_history': 'True'
        },
        'System': {
            'system_message': '''你是一个日本18+成人向游戏的中文本地化翻译程序的模块之一，你的任务是将日文文本翻译成中文。
你接收到的文本是由其他程序自动提取的，这意味着文本可能不完整。对此请同样给出不完整的翻译，保留句子与上下文衔接的空间，你翻译的文本会被重新拼接成完整的文本。
对于裸露的成人内容，请尽管使用下流、淫荡的文本，忠实地传达原文的语气和风格。\n对于大量拟声词和语气词的内容，请尽量保留原文的感觉，不要过度翻译。
对于明显是菜单、选项，以及物品、技能、地名等游戏元素的文本，请尽量保留原文意思，不要过度翻译。\n对于由片假名组成的人名、地名、技能名等，请直接音译，不要过度翻译。
请只输出翻译后的文本，不要输出任何解释、提醒或警告。'''
        },
        'Extra': {
            'group_length': '1000'
        }
    }