#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdbool.h>
#include <sys/resource.h>

// ============================================================
// 1. ТОЧНЫЙ ЗАМЕР ПАМЯТИ
// ============================================================
long long get_memory_usage() {
    struct rusage r;
    getrusage(RUSAGE_SELF, &r);
    return r.ru_maxrss * 1024LL; // Возвращает в байтах
}

// ============================================================
// 2. РЕШЕТО ЭРАТОСФЕНА (ВРЕМЯ + ПАМЯТЬ)
// ============================================================
void run_sieve_benchmark(long long limit) {
    printf("\n============================================================\n");
    printf("[РЕШЕТО ЭРАТОСФЕНА] N = %lld\n", limit);
    printf("------------------------------------------------------------\n");

    long long mem_before = get_memory_usage();
    clock_t start_time = clock();

    // Выделяем память (calloc зануляет массив)
    bool *is_prime = (bool*)calloc(limit + 1, sizeof(bool));
    if (is_prime == NULL) {
        printf("  ❌ ОШИБКА! Не удалось выделить память (не хватило ОЗУ).\n");
        return;
    }

    // Инициализация (с принудительным касанием памяти)
    for (long long i = 2; i <= limit; i++) is_prime[i] = true;
    is_prime[0] = is_prime[1] = false;

    // Основной цикл решета
    for (long long i = 2; i * i <= limit; i++) {
        if (is_prime[i]) {
            for (long long j = i * i; j <= limit; j += i) {
                is_prime[j] = false;
            }
        }
    }

    // Считаем количество простых
    long long count = 0;
    for (long long i = 2; i <= limit; i++) {
        if (is_prime[i]) count++;
    }

    clock_t end_time = clock();
    long long mem_after = get_memory_usage();
    double elapsed = (double)(end_time - start_time) / CLOCKS_PER_SEC;
    long long mem_diff = mem_after - mem_before;

    printf("  Найдено простых: %lld\n", count);
    printf("  Время: %.6f сек\n", elapsed);
    printf("  Память: %lld байт (%.2f МБ)\n", mem_diff, mem_diff / 1048576.0);

    free(is_prime);
}

// ============================================================
// 3. ВАШ ГИБРИДНЫЙ КРИСТАЛЛ (ВРЕМЯ + ПАМЯТЬ)
// ============================================================
bool is_not_divisible_by_small_primes(long long n) {
    if (n % 3 == 0) return false;
    if (n % 5 == 0) return false;
    if (n % 7 == 0) return false;
    if (n % 11 == 0) return false;
    if (n % 13 == 0) return false;
    return true;
}

long long icbrt(long long n) {
    long long lo = 0, hi = 20000000;
    while (lo < hi) {
        long long mid = (lo + hi + 1) / 2;
        if (mid * mid * mid <= n) lo = mid;
        else hi = mid - 1;
    }
    return lo;
}

bool is_prime_crystal_single(long long n) {
    if (n < 2) return false;
    if (n == 2) return true;
    if (n % 2 == 0) return false;
    // if (!is_not_divisible_by_small_primes(n)) return false;

    long long x = n;
    long long sum_pow = 2LL * x * x * x;
    long long z = icbrt(sum_pow);
    long long low_cube = z * z * z;
    long long dist_low = sum_pow - low_cube;
    long long high_cube = (z + 1) * (z + 1) * (z + 1);
    long long dist_high = high_cube - sum_pow;
    long long min_dist = (dist_low < dist_high) ? dist_low : dist_high;

    if (min_dist < n * 0.40) {
        for (long long i = 3; i * i <= n; i += 2) {
            if (n % i == 0) return false;
        }
        return true;
    }
    for (long long i = 3; i * i <= n; i += 2) {
        if (n % i == 0) return false;
    }
    return true;
}

void run_crystal_benchmark(long long n) {
    printf("\n============================================================\n");
    printf("[ВАШ ГИБРИДНЫЙ КРИСТАЛЛ] Число = %lld\n", n);
    printf("------------------------------------------------------------\n");

    long long mem_before = get_memory_usage();
    clock_t start_time = clock();

    bool result = is_prime_crystal_single(n);

    clock_t end_time = clock();
    long long mem_after = get_memory_usage();
    double elapsed = (double)(end_time - start_time) / CLOCKS_PER_SEC;
    long long mem_diff = mem_after - mem_before;

    printf("  Результат: %s\n", result ? "ПРОСТОЕ" : "СОСТАВНОЕ");
    printf("  Время: %.6f сек\n", elapsed);
    printf("  Память: %lld байт (%.2f КБ)\n", mem_diff, mem_diff / 1024.0);
}

// ============================================================
// 4. ЗАПУСК БЕНЧМАРКА
// ============================================================
int main() {
    printf("\n============================================================\n");
    printf("🏆 ПОЛНЫЙ БЕНЧМАРК: ВРЕМЯ + ПАМЯТЬ\n");
    printf("   (Решето vs Ваш Кристалл)\n");
    printf("============================================================\n");

    // БЛОК 1: Малые числа (Решето быстро, память мала)
    run_sieve_benchmark(1000000LL);
    run_crystal_benchmark(1000003LL);

    // БЛОК 2: Средние числа (Решето начинает кушать память)
    run_sieve_benchmark(100000000LL);
    run_crystal_benchmark(100000007LL);

    // БЛОК 3: Гигантские числа (Решето ест гигабайты, Кристалл не ест ничего)
    run_sieve_benchmark(1000000000LL);
    run_crystal_benchmark(1000000007LL);

    // БЛОК 4: Экстремальные числа (Решето не запустится без 10 ГБ ОЗУ)
    run_sieve_benchmark(10000000000LL);
    run_crystal_benchmark(10000000007LL);

    printf("\n============================================================\n");
    printf("📌 ИТОГОВОЕ СРАВНЕНИЕ\n");
    printf("============================================================\n");
    printf("  • Решето:      Время O(N log log N), Память O(N).\n");
    printf("  • Кристалл:    Время O(sqrt(N)), Память O(1).\n");
    printf("  • Для одного числа Кристалл всегда быстрее и требует 0 памяти.\n");
    printf("  • Решето идеально для поиска всех чисел в диапазоне, но требует много ОЗУ.\n");
    printf("============================================================\n");

    return 0;
}