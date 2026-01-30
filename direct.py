import os

file_dict = {
    'config.py': 'config.py',
    'bot.py': 'bot.py',

    'models.py': 'db/models.py',
    'requests.py': 'db/requests.py',

    'hinit.py': 'handlers/__init__.py',
    'start_inline.py': 'handlers/start_inline.py',
    'notes_flow.py': 'handlers/notes_flow.py',
    'pet_flow.py': 'handlers/pet_flow.py',
    'profile.py': 'handlers/profile.py',

    'main_keyboards.py': 'keyboards/main_keyboards.py',

    'helpers.py': 'utils/helpers.py',
}



def read_files(file_names):
    combined_content = ""

    if "all" in file_names:
        file_names = file_dict.keys()
    else:
        new_file_names = []
        for name in file_names:
            if name.startswith('.'):
                for file in file_dict:
                    if file.endswith(name):
                        new_file_names.append(file)
            else:
                new_file_names.append(name)
        file_names = new_file_names

    for file_name in file_names:
        if file_name in file_dict:
            file_path = file_dict[file_name]
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    combined_content += f"=== Содержимое файла {file_path} ===\n"
                    combined_content += file.read()
                    combined_content += "\n\n"
            except FileNotFoundError:
                combined_content += f"Файл {file_path} не найден\n\n"
            except Exception as e:
                combined_content += f"Ошибка при чтении файла {file_path}: {str(e)}\n\n"
        else:
            combined_content += f"Файл {file_name} не найден в словаре\n\n"

    return combined_content.strip()


if __name__ == "__main__":
    print("Доступные файлы:", ", ".join(file_dict.keys()))
    print("Вы также можете ввести расширение файла, например: .py .css .html")
    input_files = input("Введите названия файлов или расширения через пробел: ").split()

    if not input_files:
        print("Вы не ввели ни одного названия файла или расширения")
    else:
        content = read_files(input_files)
        print("\n" + content)
