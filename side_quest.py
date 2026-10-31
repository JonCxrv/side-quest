"""side-quest — ajuda a completar missões do Discord."""
import video

MENU = """
=== side-quest ===
1. Missões de vídeo
2. Sair
"""


def main():
    while True:
        print(MENU)
        choice = input("> ").strip()
        try:
            if choice == "1":
                video.menu()
            elif choice == "2":
                break
        except KeyboardInterrupt:
            print("\nInterrompido. Voltando ao menu.")
        except EOFError:
            break
        except Exception as err:
            print(f"\nErro: {err}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
