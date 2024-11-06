from pulp import *
import pandas as pd


def cutting_stock_optimization():
    # 1. 定义基础数据 - 使用字典便于扩展产品种类
    products = {
        'A': {'size': 20, 'demand': 80},
        'B': {'size': 40, 'demand': 150},
        'C': {'size': 32, 'demand': 132}
    }
    raw_material_length = 100

    # 2. 计算所有可能的切割方案
    max_pieces = {
        prod: raw_material_length // data['size']
        for prod, data in products.items()
    }

    # 生成所有可能的切割方案
    patterns = []
    pattern_details = []  # 存储方案详细信息

    def generate_patterns(current_pattern, remaining_length, product_keys, pattern_index):
        if not product_keys:  # 已经考虑完所有产品
            if current_pattern:  # 如果方案不为空
                patterns.append(current_pattern.copy())
                # 记录方案详细信息
                pattern_info = current_pattern.copy()
                pattern_info['waste'] = remaining_length
                pattern_info['pattern_no'] = pattern_index + 1
                pattern_details.append(pattern_info)
            return

        product = product_keys[0]
        size = products[product]['size']
        max_count = min(remaining_length // size, max_pieces[product])

        for count in range(max_count + 1):
            new_pattern = current_pattern.copy()
            new_pattern[product] = count
            new_remaining = remaining_length - (count * size)
            generate_patterns(new_pattern, new_remaining,
                              product_keys[1:], pattern_index)

    generate_patterns({prod: 0 for prod in products},
                      raw_material_length, list(products.keys()), len(patterns))

    # 3. 创建优化问题
    prob = LpProblem("Cutting_Stock_Problem", LpMinimize)

    # 4. 定义决策变量
    pattern_vars = [LpVariable(f"pattern_{i + 1}", 0, None, LpInteger)
                    for i in range(len(patterns))]

    # 5. 设置目标函数
    prob += lpSum(pattern_vars)

    # 6. 添加约束条件
    for prod in products:
        prob += lpSum(patterns[i][prod] * pattern_vars[i]
                      for i in range(len(patterns))) >= products[prod]['demand']

    # 7. 求解问题
    prob.solve()

    # 8. 输出结果
    print("\n=== 所有可能的切割方案 ===")
    df_patterns = pd.DataFrame(pattern_details)
    df_patterns = df_patterns[['pattern_no'] + list(products.keys()) + ['waste']]
    print(df_patterns)

    print("\n=== 优化结果 ===")
    print(f"状态: {LpStatus[prob.status]}")
    print(f"需要使用的原材料总数: {value(prob.objective)} 根")

    print("\n=== 最优方案组合 ===")
    total_products = {prod: 0 for prod in products}
    total_waste = 0

    for i, var in enumerate(pattern_vars):
        if value(var) > 0:
            pattern = patterns[i]
            times_used = int(value(var))
            waste = raw_material_length - sum(pattern[p] * products[p]['size']
                                              for p in products)

            print(f"\n方案 {i + 1}:")
            for prod in products:
                print(f"{prod}产品数量: {pattern[prod]}")
            print(f"废料长度: {waste}")
            print(f"使用次数: {times_used}")

            # 统计总数
            for prod in products:
                total_products[prod] += pattern[prod] * times_used
            total_waste += waste * times_used

    print("\n=== 生产统计 ===")
    for prod in products:
        print(f"{prod}产品: 实际生产 {total_products[prod]} / 需求 {products[prod]['demand']}")
    print(f"总废料长度: {total_waste}")
    print(f"平均每根原材料废料长度: {total_waste / value(prob.objective):.2f}")


if __name__ == "__main__":
    cutting_stock_optimization()
