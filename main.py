import os
import requests
import datetime
import json

now = datetime.datetime.now()
user_id = input('Введите ID пользователя vk: ')
vk_token = input('Введите vk токен: ')
ya_disk_token = input('Введите Yandex Disk токен: ')



class VkUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, version):
        self.params = {
            'access_token': token,
            'v': version
        }

    def photos_get(self, owner_id=None):
        set_number_photo = int(input('Укажите количество фотографии для копирования (по умолчанию - 5): ') or '5')
        photos_url = self.url + 'photos.get'
        photos_params = {
            'owner_id': owner_id,
            'album_id': 'profile',
            'extended': '1',
            'count': 500
        }
        res = requests.get(photos_url, params={**self.params, **photos_params}).json()
        sizes_album_list = res['response']['items']
        likes_list = []
        report_images = []
        photo_number = 0

        if not os.path.isdir('images_profile_' + owner_id):
            os.mkdir('images_profile_' + owner_id)
            print(f"\nЛокальная папка [{'images_profile_' + owner_id}] создана")
        print('\nСохранение фотографий на ПК (локально)')
        for album_list in sizes_album_list:
            response_url = requests.get((album_list['sizes'][-1]['url']), timeout=5)
            likes_number_in_photo = str(album_list['likes']['count'])
            if likes_number_in_photo not in likes_list and photo_number < set_number_photo:
                image_path = os.path.join(f'images_profile_' + owner_id, likes_number_in_photo + '.jpg')
                with open(image_path, 'bw') as image_vk:
                    image_vk.write(response_url.content)
                    likes_list.append(likes_number_in_photo)
                    report_images.append({"file_name": (likes_number_in_photo + '.jpg'),
                                          "size": album_list['sizes'][-1]['type']})
                    print(f'--> Файл {likes_number_in_photo}.jpg добавлен')
                    photo_number += 1
            elif likes_number_in_photo in likes_list and photo_number < set_number_photo:
                image_path_date = os.path.join(f'images_profile_' + owner_id,
                                               likes_number_in_photo + (now.strftime("_%d_%m_%Y")) + '.jpg')
                with open(image_path_date, 'bw') as image_vk:
                    image_vk.write(response_url.content)
                    likes_list.append(likes_number_in_photo + now.strftime("_%d_%m_%Y"))
                    report_images.append({"file_name": (likes_number_in_photo + now.strftime("_%d_%m_%Y") + '.jpg'),
                                          "size": album_list['sizes'][-1]['type']})
                    print(f'--> Файл {likes_number_in_photo}{now.strftime("_%d_%m_%Y")}.jpg добавлен')
                    photo_number += 1
            elif photo_number >= set_number_photo:
                break
        with open(owner_id + '.json', 'w') as f:
            json.dump(report_images, f, ensure_ascii=False, indent=4)
            print(f"\nФайл {owner_id + '.json'} сформирован\n")


class YandexDisk:
    def __init__(self, token):
        self.token = token

    def get_headers(self):
        return {
            'Accept': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def get_files_list(self):
        files_url = 'https://cloud-api.yandex.net/v1/disk/resources/files'
        headers = self.get_headers()
        response = requests.get(files_url, headers=headers)
        return response.json()

    def make_dir(self, dir_name):
        url_dir = "https://cloud-api.yandex.net/v1/disk/resources/"
        headers = self.get_headers()
        params = {
            'path': dir_name
        }
        requests.put(url_dir, params=params, headers=headers)

    def _get_upload_link(self, disk_file_path):
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = self.get_headers()
        params = {"path": disk_file_path, "overwrite": "true"}
        response = requests.get(upload_url, headers=headers, params=params)
        return response.json()

    def upload_file_to_disk(self, disk_file_path, filename):
        href = self._get_upload_link(disk_file_path=disk_file_path).get("href", "")
        response = requests.put(href, data=open(filename, 'rb'))
        response.raise_for_status()
        if response.status_code != 201:
            print(f'Файл {filename} не загружен!')


vk_client = VkUser(vk_token, '5.131')
# по умолчанию будут получены 5 фотографий
vk_client.photos_get(str(user_id))

ya = YandexDisk(token=ya_disk_token)
name_dir_ya_disk = 'images_profile_' + str(user_id)
list_photos_dir = os.listdir(name_dir_ya_disk)
ya.make_dir(name_dir_ya_disk)

print('Отправка фотографий на YandexDisk')
for list_photos in list_photos_dir:
    ya.upload_file_to_disk(name_dir_ya_disk + '/' + list_photos, name_dir_ya_disk + '/' + list_photos)
    print(f"--> Файл {list_photos} отправлен на YandexDisk в папку '{name_dir_ya_disk}'")

