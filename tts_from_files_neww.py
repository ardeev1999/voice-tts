# tts_from_files.py - чтение текстов из файлов
import requests
import os
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class AdvancedPoetrySynthesizer:
    def __init__(self):
        self.api_key = os.getenv('YANDEX_API_KEY')
        self.folder_id = os.getenv('YANDEX_FOLDER_ID')
        self.url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
        
        # Более подходящие настройки для поэзии
        self.voice_params = {
            'lang': 'ru-RU',
            'voice': 'filipp',      # Мужской баритон
            'speed': 0.85,          # Медленно, для поэзии
            'emotion': 'good',      # Теплая, спокойная эмоция
            'format': 'mp3',
            'sampleRateHertz': 48000,
        }
        
        print("✅ Синтезатор инициализирован")
    
    def prepare_poetic_text(self, text):
        """
        Подготовка текста для поэтического чтения БЕЗ озвучивания пауз
        """
        # Убираем лишние пробелы и переносы
        text = text.strip()
        
        # Разделяем на строки
        lines = text.split('\n')
        processed_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:  # Пустая строка
                # Для пустых строк добавляем ТОЛЬКО пробелы (тихая пауза)
                processed_lines.append(' ')
                continue
            
            # Обрабатываем ударения (важно для интонации)
            line = self._add_stresses(line)
            
            # Добавляем строку
            processed_lines.append(line)
            
            # Если это НЕ последняя строка и следующая НЕ пустая
            if i < len(lines) - 1 and lines[i + 1].strip():
                # Добавляем точку с запятой для естественной паузы
                processed_lines.append('; ')
            else:
                processed_lines.append(' ')
        
        # Собираем обратно
        result = ''.join(processed_lines)
        
        # Заменяем многоточия (они дают естественную паузу)
        result = result.replace('...', '…')
        
        return result
    
    def _add_stresses(self, text):
        """Добавление ударений для правильного произношения"""
        stresses = {
            "персть": "пе́рсть",
            "копытом": "копы́том",
            "умыта": "умы́та",
            "Пичковке": "Пичко́вке",
            "Нарьян-Мар": "Нарья́н-Ма́р",
            "огонь": "ого́нь",
            "лошадь": "ло́шадь",
            "метели": "метели́",
            "локонам": "ло́конам",
        }
        
        for word, stressed in stresses.items():
            text = text.replace(word, stressed)
        
        return text
    
    def synthesize_from_text(self, text, filename, use_poetic=True):
        """Синтез из текстовой переменной"""
        print(f"\n🎙️  Синтез: {filename}")
        print(f"   Длина текста: {len(text)} символов")
        
        if use_poetic:
            prepared_text = self.prepare_poetic_text(text)
        else:
            prepared_text = text
        
        headers = {'Authorization': f'Api-Key {self.api_key}'}
        data = {
            'text': prepared_text,
            **self.voice_params,
            'folderId': self.folder_id,
        }
        
        try:
            response = requests.post(self.url, headers=headers, data=data, stream=True)
            
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                size = os.path.getsize(filename)
                print(f"✅ Успешно: {filename} ({size:,} байт)")
                return True
            else:
                print(f"❌ Ошибка {response.status_code}: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False
    
    def synthesize_from_file(self, input_file, output_file=None, use_poetic=True):
        """Чтение текста из файла и синтез в MP3"""
        
        # Определяем имя выходного файла
        if not output_file:
            output_file = Path(input_file).stem + '.mp3'
        
        # Читаем текст из файла
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                text = f.read()
        except UnicodeDecodeError:
            # Пробуем другую кодировку
            with open(input_file, 'r', encoding='cp1251') as f:
                text = f.read()
        except Exception as e:
            print(f"❌ Ошибка чтения файла {input_file}: {e}")
            return False
        
        return self.synthesize_from_text(text, output_file, use_poetic)
    
    def batch_synthesize_folder(self, input_folder='texts', output_folder='audio'):
        """Синтез всех текстовых файлов из папки"""
        
        input_path = Path(input_folder)
        output_path = Path(output_folder)
        
        # Создаем папки если их нет
        input_path.mkdir(exist_ok=True)
        output_path.mkdir(exist_ok=True)
        
        print(f"\n📁 Синтез всех файлов из: {input_folder}/")
        
        # Ищем все текстовые файлы
        text_files = list(input_path.glob('*.txt'))
        
        if not text_files:
            print(f"❌ В папке {input_folder} нет .txt файлов")
            print(f"   Создайте файлы с текстом ")
            return []
        
        results = []
        for text_file in text_files:
            print(f"\n{'='*50}")
            print(f"📖 Файл: {text_file.name}")
            
            output_file = output_path / f"{text_file.stem}.mp3"
            
            success = self.synthesize_from_file(
                input_file=str(text_file),
                output_file=str(output_file),
                use_poetic=True
            )
            
            if success:
                results.append((text_file.name, str(output_file)))
            
            # Пауза между запросами (чтобы не перегружать API)
            time.sleep(1)
        
        # Создаем отчет
        self._create_report(results, output_folder)
        
        return results
    
    def _create_report(self, results, output_folder):
        """Создание отчета о созданных файлах"""
        report_file = f"{output_folder}/_отчет.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("ОТЧЕТ О СИНТЕЗЕ \n")
            f.write("="*50 + "\n\n")
            f.write(f"Дата: {time.strftime('%d.%m.%Y %H:%M')}\n")
            f.write(f"Всего файлов: {len(results)}\n\n")
            
            for i, (input_name, output_path) in enumerate(results, 1):
                size = os.path.getsize(output_path)
                f.write(f"{i}. {input_name}\n")
                f.write(f"   → {Path(output_path).name} ({size:,} байт)\n\n")
        
        print(f"\n📄 Отчет создан: {report_file}")


# ============================================================================
# ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ
# ============================================================================

def create_template_files():
    """Создание шаблонных файлов для озвучивания"""

    # Создаем папку для текстов
    texts_dir = Path('texts')
    texts_dir.mkdir(exist_ok=True)

    # Шаблоны файлов
    templates = {
          '01_приветствие.txt': """Здравствуйте! Это тестовое приветствие, созданное для проверки синтеза речи. 
Текст может быть любым: от делового сообщения до личного поздравления. 
Главное — он звучит естественно и понятно.""",

        '02_стихотворение.txt': """Вот небольшой пример поэтического текста.
Он позволяет оценить интонации и ритм синтезатора.
Пусть эти строки прозвучат плавно и выразительно,
с нужными паузами и смысловыми акцентами.""",

        '03_инструкция.txt': """Этот файл показывает, как можно использовать синтезатор для озвучивания инструкций.
Например, вы можете создать голосовое сопровождение для презентации,
озвучить учебный материал или просто записать заметку.
Возможности ограничены только вашей фантазией."""
    }
    
    print("📝 Создаю шаблонные файлы...")
    
    for filename, content in templates.items():
        filepath = texts_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   ✅ Создан: {filename}")
    
    print(f"\n📁 Файлы сохранены в папке: {texts_dir}/")
    print("✏️  Вы можете редактировать эти файлы или добавлять свои")


def main():
    """Основная функция"""
    
    print("СЕРВИС ОЗВУЧКИ ТЕКСТА ИЗ ФАЙЛОВ")
    print("="*50)
    
    # Создаем синтезатор
    synthesizer = AdvancedPoetrySynthesizer()
    
    # Создаем шаблоны файлов (если нужно)
    print("\n1. Хотите создать шаблонные файлы?")
    choice = input("   (y/n, Enter = y): ").strip().lower()
    
    if choice in ['', 'y', 'yes', 'да']:
        create_template_files()
    
    print("\n2. Выберите режим работы:")
    print("   1 - Синтез всех файлов из папки 'texts/'")
    print("   2 - Синтез одного конкретного файла")
    print("   3 - Синтез текста из командной строки")
    
    mode = input("   Ваш выбор (1-3): ").strip()
    
    if mode == '1':
        # Режим 1: Синтез всех файлов из папки
        print("\n🔄 Запускаю синтез всех файлов из папки 'texts/'...")
        results = synthesizer.batch_synthesize_folder()
        
        if results:
            print(f"\n🎉 Готово! Создано {len(results)} аудиофайлов в папке 'audio/'")
            print("🎧 Проверьте созданные файлы")
    
    elif mode == '2':
        # Режим 2: Синтез одного файла
        print("\n📄 Введите путь к текстовому файлу:")
        filepath = input("   Например: texts/название_файла.txt\n   > ").strip()
        
        if not filepath:
            filepath = 'texts/название_файла.txt'
        
        if os.path.exists(filepath):
            output_file = Path(filepath).stem + '.mp3'
            synthesizer.synthesize_from_file(filepath, output_file)
        else:
            print(f"❌ Файл не найден: {filepath}")
    
    elif mode == '3':
        # Режим 3: Прямой ввод текста
        print("\n📝 Введите текст для синтеза (Ctrl+Z, Enter для завершения):")
        print("   (Или просто нажмите Enter для тестового текста)")
        
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        
        text = '\n'.join(lines) if lines else "Тестовый текст для синтеза речи."
        
        filename = input("\n💾 Имя выходного файла (например: название.mp3): ").strip()
        if not filename:
            filename = 'синтез_из_текста.mp3'
        
        synthesizer.synthesize_from_text(text, filename)
    
    else:
        print("\n⚠️  Неверный выбор. Запускаю режим по умолчанию...")
        # Запускаем синтез всех файлов
        results = synthesizer.batch_synthesize_folder()
    
    print("\n" + "="*50)
    print("✨ Программа завершена!")
    print("   Аудиофайлы готовы ")


if __name__ == "__main__":
    main()
    input("\nНажмите Enter для выхода...")