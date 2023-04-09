import os
import json

import requests
from pprint import pprint
from datetime import datetime
from tqdm import tqdm


class VKUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, version):
        self.params = {
            'v': version,
            'access_token': token
        }

    def get_photos(self, id, count):
        """
        Получаем список из словарей с параметрами фотографий: photos_list
        """
        photo_get_params = {
            'owner_id': id,
            'album_id': 'profile',
            'extended': '1',
            'photo_sizes': '1',
            'count': count
        }
        URL = self.url + 'photos.get'

        res = requests.get(URL, params={**self.params, **photo_get_params})
        photos_list = res.json()['response']['items']
        return photos_list

    def get_res_list(self, id, count):
        """
        Перебираем получившиеся словари поочереди с помощью цикла for, для каждой фото находим число лайков и дату
        выгрузки.

        В следующих циклах for сравниваем параметр величины фото со стандартными в порядке уменьшения размера.
        Как только нашли самое большое фото - прервали цикл. При этом записываем в итоговый список res_list словарь
        с параметрами (имя, лайки, дата загрузки, тип размера). Если имя уже встречалось в name_list, добавляем дату.
        """

        res_list = []
        name_list = []
        for photo in self.get_photos(id, count):
            flag = False
            unix = int(photo['date'])
            dttime = datetime.utcfromtimestamp(unix).strftime('%d.%m.%Y')
            likes_count = photo['likes']['count']

            for size in ['w', 'z', 'y', 'x', 'r', 'q', 'p', 'o', 'm', 's']:
                for params in photo['sizes']:
                    if params['type'] == size:

                        if likes_count not in name_list:
                            res_list.append({'file_name': f"{likes_count}.jpg", 'date': dttime, 'size': size,
                                             'url': params['url']})
                            name_list.append(likes_count)
                        else:
                            res_list.append({'file_name': f"{likes_count}_{dttime}.jpg", 'size': size,
                                             'url': params['url']})

                        flag = True
                        break
                if flag:
                    flag = False
                    break
        return res_list
    

    def create_json(self, id, count):
        res = []
        for photo in self.get_res_list(id, count):
            data_dict = {'file_name': photo['file_name'], 'size': photo['size']}
            res.append(data_dict)
        with open(f'{os.getcwd()}/res.json', 'w') as res_file:
            json.dump(res, res_file, ensure_ascii='False', indent=2)
        return 'Файл res.json записан успешно'


class YandexDisk:
    url_yandex = 'https://cloud-api.yandex.net/'

    def __init__(self, token):
        self.token = token


    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': f'OAuth {self.token}',
            'Accept': 'application/json'
        }
    

    def create_folder(self, disk_folder):
        """
        Создаем папку на Яндекс-диске для загрузки фотографий
        """
        headers = self.get_headers()
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        params = {'path': disk_folder}
        requests.put(url, headers=headers, params=params)
       
        return disk_folder


    def upload_file_to_disk(self, disk_folder, res_list):
        '''
        Загружаем файлы, полученные из VK, в выбранную папку folder на Яндекс-диске
        '''
        headers = self.get_headers()
               
        for photo in tqdm(res_list, desc='Загружено фото', unit='photo'):
            params = {'path': f"{disk_folder}/{photo['file_name']}",
                  'url': photo['url'],
                  'overwrite': 'false'
            }
            requests.post(f'{self.url_yandex}v1/disk/resources/upload', headers=headers, params=params)            
            tqdm.write(f"Файл {photo['file_name']} загружен", end='\n')


if __name__ == '__main__':

    print(f'Добавьте в директорию {os.getcwd()} файлы, содержащие ключи доступа (token_VK.txt, token_YDisk.txt)')
    
    with open('token_VK.txt') as file:
        vk_token = file.read().strip()
    with open('token_YDisk.txt') as file_:
        ya_token = file_.read().strip()
    
    v = input('Введите версию API (по умолчанию версия 5.131): ')
    if not v:
        vk_maksim = VKUser(vk_token, '5.131')
    else:
        vk_maksim = VKUser(vk_token, v)
    
    id, count = input('Введите id пользователя: '), int(input('Введите количество фотографий для выгрузки: '))
    print(vk_maksim.create_json(id, count))
    # id = '792906514', count = 5
    res_list = vk_maksim.get_res_list(id, count)
    
    ya = YandexDisk(ya_token)

    folder = input('Введите папку на Яндекс-диске: ')
    ya.create_folder(folder)
    ya.upload_file_to_disk(folder, res_list)

