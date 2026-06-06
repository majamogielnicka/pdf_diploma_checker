import llama_cpp

def check_cuda():
    '''
    wejscie: brak.
    wyjscie: brak (wyświetla komunikaty w konsoli).
    opis: Sprawdza, czy biblioteka llama.cpp jest poprawnie skompilowana z obsługą karty graficznej (CUDA).
    '''
    print("Sprawdzanie informacji o systemie z llama.cpp...")
    sys_info = llama_cpp.llama_print_system_info().decode('utf-8')
    
    print("\n--- SUROWE DANE ---")
    print(sys_info)
    print("-------------------\n")
    
    if "CUDA = 1" in sys_info:
        print("✅ SUKCES: Twoja biblioteka llama-cpp-python WIDZI kartę graficzną (CUDA)!")
    else:
        print("❌ BŁĄD: Twoja biblioteka jest skompilowana TYLKO na procesor (CPU).")
        print("Parametr n_gpu_layers będzie ignorowany.")

if __name__ == "__main__":
    check_cuda()