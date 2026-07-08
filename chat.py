import time
from agent import ask_agent


def print_sources(sources):
    if not sources:
        return

    print("\nИсточники:")
    print("-" * 60)

    for i, source in enumerate(sources, 1):
        print(f"\n{i}. {source.get('section', 'Раздел')}")

        if source.get("warning"):
            print("ВНИМАНИЕ")

        if source.get("prohibited"):
            print("ЗАПРЕТ")

        print(source.get("content", ""))


def main():
    print("=" * 60)
    print("Коммерческий ИИ-помощник")
    print("Введите вопрос или 'exit' для выхода.")
    print("=" * 60)

    while True:
        question = input("\nВы: ").strip()

        if question.lower() in ("exit", "quit", "выход"):
            print("Завершение работы.")
            break

        if not question:
            continue

        print("\nОбработка запроса...")

        start = time.time()

        try:
            response = ask_agent(question)

            elapsed = time.time() - start

            print("\nОтвет:")
            print("-" * 60)
            print(response.get("answer", "Ответ отсутствует"))

            print_sources(response.get("sources", []))

            print(f"\nВремя ответа: {elapsed:.2f} сек.")

        except Exception as e:
            print("\nОшибка:")
            print(e)


if __name__ == "__main__":
    main()