import csv
import os.path
from datetime import date
import json


def output_chat_info():
    global chat
    
    print(chat['name'], chat['type'], chat['id'], sep=' | ')
    print(len(chat['messages']), 'сообщений всего')
    print(len([chat['messages'][i]['id']
               for i in range(len(chat['messages']))
               if chat['messages'][i]['type'] == 'service']),
          'из них сервисные', end='\n\n\n')
    
    fields = set()
    k = 0
    mess_id = []
    for i in range(len(chat['messages'])):
        if chat['messages'][i]['type'] == 'message':
            fields.add(tuple(chat['messages'][i].keys()))
            if k < len(fields):
                mess_id.append(i)
                k += 1
    
    print(k, "различных наборов полей")
    print(*zip(mess_id, fields), sep='\n', end='\n\n\n')
    
    fields = [set(m) for m in fields]
    required_keys = fields[0]
    all_keys = fields[0]
    for m in fields[1:]:
        required_keys = required_keys.intersection(m)
        all_keys = all_keys.union(m)
    
    print('\tОбязательные поля:', required_keys, end='\n\n\n')
    
    unique_types = set()
    reacts = set()
    for i in range(len(chat['messages'])):
        if chat['messages'][i]['text_entities']:
            for j in range(len(chat['messages'][i]['text_entities'])):
                unique_types.add(
                    chat['messages'][i]['text_entities'][j]['type'])
        
        if 'reactions' in chat['messages'][i]:
            for r in chat['messages'][i]['reactions']:
                if r['type'] == 'emoji':
                    reacts.add(r['emoji'])
                else:
                    reacts.add(r['document_id'])
    

def output_all_messages():
    global chat
    
    k = 0
    for i in range(len(chat['messages'])):
        if chat['messages'][i]['type'] == 'message':
            # если опрос, то пропускаем
            if chat['messages'][i].get('poll'):
                continue
            
            # если есть ответ на другое сообщение
            if chat['messages'][i].get('reply_to_message_id'):
                repi = i - 1
                while chat['messages'][repi]['id'] > chat['messages'][i]['reply_to_message_id']:
                    repi -= 1
                
                # если сообщение, на которое отвечают, не сервисное
                if chat['messages'][repi]['type'] == 'message':
                    print('\t', chat['messages'][repi]['from'])
                    # except KeyError:
                    #     print('\t', chat['messages'][repi])
                    
                    # обрабатываем текст первого сообщение
                    text = chat['messages'][repi]['text']
                    if isinstance(text, list):
                        cooked_text = ''
                        for item in text:
                            if isinstance(item, str):
                                cooked_text += item
                            elif isinstance(item, dict):
                                cooked_text += item['text']
                                if item.get('href'):
                                    cooked_text += ' ' + item['href'] + ' '
                        
                        text = cooked_text
                    elif not text and chat['messages'][repi].get('media_type'):
                        if chat['messages'][repi]['media_type'] == 'sticker':
                            print('File:',  '<' + chat['messages'][repi]['file'] + '>')
                    
                    print('\t', text, end='\n/////////////////////\n')
            
            print(chat['messages'][i]['id'])
            print(':' + chat['messages'][i]['from'] + ':', end=' ')
            print(chat['messages'][i]['from_id'][4:]
                  if chat['messages'][i]['from_id'].startswith('user')
                  else chat['messages'][i]['from_id'][7:])
            print('Дата:', chat['messages'][i]['date'] + ',',
                  'unix:', chat['messages'][i]['date_unixtime'],
                  end='\n')
            
            if chat['messages'][i].get('edited'):
                print('Изменено:', chat['messages'][i]['edited'] + ',',
                      'unix:', chat['messages'][i]['edited_unixtime'],
                      end='\n\n')
            
            # обрабатываем текст основного сообщения
            text = chat['messages'][i]['text']
            if isinstance(text, list):
                cooked_text = ''
                for item in text:
                    if isinstance(item, str):
                        cooked_text += item
                    elif isinstance(item, dict):
                        cooked_text += item['text']
                        if item.get('href'):
                            cooked_text += ' ' + item['href'] + ' '
                
                text = cooked_text
            elif not text and chat['messages'][i].get('media_type'):
                if chat['messages'][i]['media_type'] == 'sticker':
                    print('File:', '<' + chat['messages'][i]['file'] + '>')
            elif not text and not chat['messages'][i].get('media_type'):
                continue
            
            print(text, end='\n' + '-' * 20 + '\n')
            k += 1
    
    print(k, 'сообщений будет задействовано в датасете')


def json_chat_to_csv(file='chat_data/ChatExport_2024-11-08/result.json'):
    folder = os.path.dirname(file) + "/"
    chat = json.load(open(file, encoding='utf-8'))
    csv_data = [['id', 'from_id', 'date', 'text', 'edited', 'reply_to_id']]
    members = {}
    reactions = [['id', "emoji", 'document_id']]
    members_reactions = [['message_id', 'reaction_id', 'member_id',  'date']]
    all_reactions = ['']
    
    for i in range(len(chat['messages'])):
        if chat['messages'][i]['type'] == 'message':
            # если опрос, то пропускаем
            if chat['messages'][i].get('poll'):
                continue
            
            line = [
                chat['messages'][i]['id'],
                # chat['messages'][i]['from_id'][4:]
                # if chat['messages'][i]['from_id'].startswith('user')
                # else chat['messages'][i]['from_id'][7:],
                chat['messages'][i]['forwarded_from']
                if ('forwarded_from' in chat['messages'][i]
                    and chat['messages'][i]
                    ['forwarded_from'] != chat['messages'][i]['from']
                    and chat['messages'][i]['forwarded_from'])
                else chat['messages'][i]['from_id'],
                chat['messages'][i]['date']
            ]
            
            # обрабатываем текст основного сообщения
            text = chat['messages'][i]['text_entities']
            if text:
                cooked_text = ''
                for item in text:
                    if item['type'] in [
                        'plain', 'strikethrough', 'underline', 'bold',
                        'hashtag', 'mention_name', 'spoiler', 'italic',
                        'custom_emoji', 'mention', 'blockquote'
                        ]:
                        cooked_text += item['text']
                
                if text[0]['type'] == 'custom_emoji':
                    cooked_text = 'File: <' + text[0]['document_id'] + '>'
             
                text = cooked_text.strip()
            elif not text and chat['messages'][i].get('media_type'):
                # сохраняю отправленные стикеры,
                # чтобы из можно было распознать по шаблону
                # среди обычных сообщений
                if chat['messages'][i]['media_type'] == 'sticker':
                    text = ('File: <' + folder + chat['messages'][i]['file'] + '>')
                else:
                    continue

            if not text:
                continue
            
            line.append(text)
            line.append(chat['messages'][i].get('edited_unixtime', ''))
            # Стоит проверить на существование сообщений,
            # на которые даётся ответ
            line.append(chat['messages'][i].get('reply_to_message_id', ''))
            
            csv_data.append(line)
            
            members[chat['messages'][i]['from_id']] = chat['messages'][i]['from']
            
            if ('forwarded_from' in chat['messages'][i]
               and chat['messages'][i]['forwarded_from'] != chat['messages'][i]['from']
               and chat['messages'][i]['forwarded_from']):
                members[chat['messages'][i]['forwarded_from']] = chat['messages'][i]['forwarded_from']
            
            if 'reactions' in chat['messages'][i]:
                for r in chat['messages'][i]['reactions']:
                    if (r['type'] == 'emoji' and not any(r['emoji'] == ri[1] 
                                                         for ri in reactions[1:])):
                        reactions.append([len(reactions), r['emoji'], None])
                        all_reactions.append(r['emoji'])
                    elif (r['type'] == 'custom_emoji' and not any(folder + r['document_id'] == ri[2] 
                                                                  for ri in reactions[1:])):
                        reactions.append([len(reactions), None, folder + r['document_id']])
                        all_reactions.append(folder + r['document_id'])
                    
                    ri = all_reactions.index(r['emoji']
                                             if r['type'] == 'emoji'
                                             else folder + r['document_id'])
                    
                    if 'recent' in r:
                        for m in r['recent']:
                            members_reactions.append([
                                chat['messages'][i]['id'], ri,
                                m['from_id'], m['date']
                            ])
                        
                        for _ in range(r['count'] - len(r['recent'])):
                            members_reactions.append([
                                chat['messages'][i]['id'], ri,
                                None, None
                            ])
                    else:
                        for _ in range(r['count']):
                            members_reactions.append([
                                chat['messages'][i]['id'], ri,
                                None, None
                            ])
            
    # print(*csv_data, sep='\n')
    
    id_list = [l[0] for l in csv_data[1:]]
    # reply_to_delete = []
    for i, l in enumerate(csv_data[1:]):
        if l[-1] and l[-1] not in id_list:
            csv_data[i + 1][-1] = None
    #         reply_to_delete.append(i + 1)
    #         # csv_data[i][-1] = ''
    
    # print(f'{len(reply_to_delete)} из {len(csv_data)} сообщений удалены'
    #       ' из-за отсутствия контекста ответов')
    
    # print(k, 'ответов на сообщения (reply_to_id) помечены пустыми '
    #          'из-за отсутствия сообщений, к которым приложен ответ')
    
    # Удаляем дубликаты пользователей
    memdel = []
    for uid, uname in list(members.items()):
        if (list(members.values()).count(uname) > 1
           and not (uid.startswith('channel') or uid.startswith('user'))):
            memdel.append(uid)
            
    members = [['user_id', 'username']] + [
            [uid, uname] for uid, uname in list(members.items()) if uid not in memdel
        ]
    print(*members, sep='\n')
    
    with open(f'chat_data/chat_members {date.today()}.csv', mode='w', 
              newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(members)
    
    print('csv файл с пользователями успешно создан')
    
    # csv_data = [l for i, l in enumerate(csv_data)]
    #             if i not in reply_to_delete]
    
    for i, line in enumerate(csv_data[1:]):
        try:
            if line[1] in memdel:
                for j in range(1, len(members)):
                    if members[j][1] == line[1]:
                        print(csv_data[i + 1], members[j][0])
                        csv_data[i + 1][1] = members[j][0]
                        break
                        
        except AttributeError:
            print(line)
            raise

    # csv_data = [csv_data[0]] + [[l[0], new_user_id[l[1]], *l[2:]]
    #                             for l in csv_data[1:]]
    print(*csv_data[-10:], sep='\n')
    
    with open(f'chat_data/chat_history {date.today()}.csv', mode='w',
              newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(csv_data)
    
    print('csv файл с сообщениями успешно создан\n')
    
    if len(members_reactions) > 1:
        # members_reactions = ([members_reactions[0]]
        #                      + [l1 for l1 in members_reactions[1:]
        #                     if id_list.index(l1[0]) not in reply_to_delete])
        
        with (open(f'chat_data/reactions {date.today()}.csv', 'w',
                   newline='', encoding='utf-8') as r,
              open(f'chat_data/members_reactions {date.today()}.csv', 'w',
                   newline='', encoding='utf-8') as mr):
            writer = csv.writer(r)
            writer.writerows(reactions)
            writer = csv.writer(mr)
            writer.writerows(members_reactions)
    
        print('csv файлы с реакциями участников чата созданы \n')

def json_supergroup_to_csv(file='chat_data\ChatExportSlizerin_2024-12-27\\result.json'):
    folder = os.path.dirname(file) + "/"
    chat = json.load(open(file, encoding='utf-8'))
    csv_data = [['id', 'from_id', 'date', 'text',
                 'edited', 'reply_to_id', 'topic']]
    members = {}
    topics = {}
    reactions = [['id', "emoji", 'document_id']]
    members_reactions = [['message_id', 'reaction_id', 'member_id',
                          'date']]
    all_reactions = ['']
    
    for i in range(len(chat['messages'])):
        if chat['messages'][i]['type'] == 'service' and chat['messages'][i]["action"] == "topic_created":
            topics[chat['messages'][i]['id']] = chat['messages'][i]['title']

        if chat['messages'][i]['type'] == 'message':
            # если опрос, то пропускаем
            if chat['messages'][i].get('poll'):
                continue
            
            line = [
                chat['messages'][i]['id'],
                # chat['messages'][i]['from_id'][4:]
                # if chat['messages'][i]['from_id'].startswith('user')
                # else chat['messages'][i]['from_id'][7:],
                chat['messages'][i]['forwarded_from']
                if ('forwarded_from' in chat['messages'][i]
                    and chat['messages'][i]
                    ['forwarded_from'] != chat['messages'][i]['from']
                    and chat['messages'][i]['forwarded_from'])
                else chat['messages'][i]['from_id'],
                chat['messages'][i]['date']
            ]
            
            # обрабатываем текст основного сообщения
            text = chat['messages'][i]['text_entities']
            if text:
                cooked_text = ''
                for item in text:
                    if item['type'] in [
                        'plain', 'strikethrough', 'underline', 'bold',
                        'hashtag', 'mention_name', 'spoiler', 'italic',
                        'custom_emoji', 'mention', 'blockquote'
                    ]:
                        cooked_text += item['text']
                
                if len(text) == 1 and text[0]['type'] == 'custom_emoji':
                    cooked_text = 'File: <' + text[0]['document_id'] + '>'
             
                text = cooked_text.strip()
            elif not text and chat['messages'][i].get('media_type'):
                # сохраняю отправленные стикеры,
                # чтобы из можно было распознать по шаблону
                # среди обычных сообщений
                if chat['messages'][i]['media_type'] == 'sticker':
                    text = 'File: <' + folder + chat['messages'][i]['file'] + '>'
                else:
                    continue

            if not text:
                continue
            
            line.append(text)
            line.append(chat['messages'][i].get('edited_unixtime', ''))
            # Стоит проверить на существование сообщений,
            # на которые даётся ответ
            line.append(chat['messages'][i].get(
                'reply_to_message_id', ''))
            
            # Обрабатываем reply для определения, ссылается сообщение на тему или пользователя
            if line[-1] is not None:
                if line[-1] in topics:
                    line.append(line[-1])
                    line[-2] = None
                else:
                    for ln in csv_data[::-1]:
                        if ln[0] == line[-1]:
                            line.append(ln[-1])
                            break
            
            print()
            csv_data.append(line)
            
            members[chat['messages'][i]['from_id']] = chat['messages'][i]['from']
            
            if ('forwarded_from' in chat['messages'][i]
               and chat['messages'][i]['forwarded_from'] != chat['messages'][i]['from']
               and chat['messages'][i]['forwarded_from']):
                members[chat['messages'][i]
                        ['forwarded_from']] = chat['messages'][i]['forwarded_from']
            
            if 'reactions' in chat['messages'][i]:
                for r in chat['messages'][i]['reactions']:
                    if (r['type'] == 'emoji' and not any(r['emoji'] == ri[1] 
                                                         for ri in reactions[1:])):
                        reactions.append([len(reactions), r['emoji'], None])
                        all_reactions.append(r['emoji'])
                    elif (r['type'] == 'custom_emoji' and not any(folder + r['document_id'] == ri[2] 
                                                                  for ri in reactions[1:])):
                        reactions.append([len(reactions), None, folder + r['document_id']])
                        all_reactions.append(folder + r['document_id'])
                    
                    ri = all_reactions.index(r['emoji']
                                             if r['type'] == 'emoji'
                                             else folder + r['document_id'])
                    
                    if 'recent' in r:
                        for m in r['recent']:
                            members_reactions.append([chat['messages'][i]['id'], ri, m['from_id'], m['date']])
                        
                        for _ in range(r['count'] - len(r['recent'])):
                            members_reactions.append([chat['messages'][i]['id'], ri, None, None])
                    else:
                        for _ in range(r['count']):
                            members_reactions.append([chat['messages'][i]['id'], ri, None, None])
            
    # print(*csv_data, sep='\n')
    
    id_list = [l[0] for l in csv_data[1:]]
    # reply_to_delete = []
    for i, l in enumerate(csv_data[1:]):
        if l[-2] and l[-2] not in id_list:
            csv_data[i + 1][-2] = None
    #         reply_to_delete.append(i + 1)
            # csv_data[i][-1] = ''
    
    # print(f'{len(reply_to_delete)} из {len(csv_data)} сообщений удалены'
    #       ' из-за отсутствия контекста ответов')
    
    # print(k, 'ответов на сообщения (reply_to_id) помечены пустыми '
    #          'из-за отсутствия сообщений, к которым приложен ответ')
    
    # Удаляем дубликаты пользователей
    memdel = []
    for uid, uname in list(members.items()):
        if (list(members.values()).count(uname) > 1 
           and not (uid.startswith('channel') or uid.startswith('user'))):
            memdel.append(uid)
            
    members = [['user_id', 'username']] + [
            [uid, uname] for uid, uname in list(members.items()) if uid not in memdel
        ]
    print(*members, sep='\n')
    
    with open(f'chat_data/chat_members {date.today()}.csv', mode='w',
              newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(members)
    
    print('csv файл с пользователями успешно создан')
    
    # csv_data = [l for i, l in enumerate(csv_data)
    #             if i not in reply_to_delete]
    
    for i, line in enumerate(csv_data[1:]):
        try:
            if line[1] in memdel:
                for j in range(1, len(members)):
                    if members[j][1] == line[1]:
                        print(csv_data[i + 1], members[j][0])
                        csv_data[i + 1][1] = members[j][0]
                        break
                        
        except AttributeError:
            print(line)
            raise

    # csv_data = [csv_data[0]] + [[l[0], new_user_id[l[1]], *l[2:]]
    #                             for l in csv_data[1:]]
    print(*csv_data[-10:], sep='\n')
    
    with open(f'chat_data/chat_history {date.today()}.csv', mode='w',
              newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(csv_data)
    
    with open(f'chat_data/chat_topics {date.today()}.csv', mode='w',
              newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows([['topic_id', 'topic']] + list(topics.items()))
    
    print('csv файл с сообщениями успешно создан\n')
    
    if len(members_reactions) > 1:
        # members_reactions = ([members_reactions[0]]
        #                      + [l1 for l1 in members_reactions[1:]
        #                     if id_list.index(l1[0]) not in reply_to_delete])
        
        with (open(f'chat_data/reactions {date.today()}.csv', 'w',
                   newline='', encoding='utf-8') as r,
              open(f'chat_data/members_reactions {date.today()}.csv', 'w',
                   newline='', encoding='utf-8') as mr):
            writer = csv.writer(r)
            writer.writerows(reactions)
            writer = csv.writer(mr)
            writer.writerows(members_reactions)
    
        print('csv файлы с реакциями участников чата созданы \n')

if __name__ == '__main__':
    chat = json.load(open('chat_data/ChatExport_2024-11-08/result.json',
                          encoding='utf-8'))
    # output_chat_info()
    # output_all_messages()
    
    # json_chat_to_csv('chat_data/ChatExport_2024-11-08/result.json')
    json_chat_to_csv('chat_data\ChatExportSuetologi_2025-01-10\\result.json')
