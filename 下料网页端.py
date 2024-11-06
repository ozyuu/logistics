import streamlit as st
from pulp import *
import pandas as pd


def cutting_stock_optimization(products, raw_material_length):
    # 计算所有可能的切割方案
    max_pieces = {
        prod: raw_material_length // data['size']
        for prod, data in products.items()
    }

    patterns = []
    pattern_details = []

    def generate_patterns(current_pattern, remaining_length, product_keys, pattern_index):
        if not product_keys:
            if current_pattern:
                patterns.append(current_pattern.copy())
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
            generate_patterns(new_pattern, new_remaining, product_keys[1:], pattern_index)

    generate_patterns({prod: 0 for prod in products}, raw_material_length, list(products.keys()), len(patterns))

    prob = LpProblem("Cutting_Stock_Problem", LpMinimize)
    pattern_vars = [LpVariable(f"pattern_{i + 1}", 0, None, LpInteger) for i in range(len(patterns))]
    prob += lpSum(pattern_vars)

    for prod in products:
        prob += lpSum(patterns[i][prod] * pattern_vars[i] for i in range(len(patterns))) >= products[prod]['demand']

    prob.solve()

    results = {
        'status': LpStatus[prob.status],
        'total_materials': value(prob.objective),
        'patterns': pattern_details,
        'optimal_solution': [],
        'total_products': {prod: 0 for prod in products},
        'total_waste': 0
    }

    for i, var in enumerate(pattern_vars):
        if value(var) > 0:
            pattern = patterns[i]
            times_used = int(value(var))
            waste = raw_material_length - sum(pattern[p] * products[p]['size'] for p in products)

            solution_detail = {
                'pattern_no': i + 1,
                'products': pattern,
                'waste': waste,
                'times_used': times_used
            }
            results['optimal_solution'].append(solution_detail)

            for prod in products:
                results['total_products'][prod] += pattern[prod] * times_used
            results['total_waste'] += waste * times_used

    return results


def main():
    st.title("切割优化计算器")

    st.sidebar.header("参数设置")
    raw_material_length = st.sidebar.number_input("原材料长度", value=100)

    st.sidebar.header("产品设置")
    n_products = st.sidebar.number_input("产品种类数量", min_value=1, max_value=10, value=3)

    products = {}
    for i in range(int(n_products)):
        st.sidebar.subheader(f"产品 {chr(65 + i)}")
        size = st.sidebar.number_input(f"产品{chr(65 + i)}长度", value=20 + i * 10, key=f"size_{i}")
        demand = st.sidebar.number_input(f"产品{chr(65 + i)}需求量", value=80 + i * 20, key=f"demand_{i}")
        products[chr(65 + i)] = {'size': size, 'demand': demand}

    if st.button("开始计算"):
        results = cutting_stock_optimization(products, raw_material_length)

        st.header("计算结果")
        st.write(f"优化状态: {results['status']}")
        st.write(f"需要原材料总数: {results['total_materials']} 根")

        st.subheader("所有可能的切割方案")
        df_patterns = pd.DataFrame(results['patterns'])
        st.dataframe(df_patterns)

        st.subheader("最优方案组合")
        for solution in results['optimal_solution']:
            st.write(f"\n方案 {solution['pattern_no']}:")
            for prod, count in solution['products'].items():
                st.write(f"{prod}产品数量: {count}")
            st.write(f"废料长度: {solution['waste']}")
            st.write(f"使用次数: {solution['times_used']}")

        st.subheader("生产统计")
        for prod in products:
            st.write(f"{prod}产品: 实际生产 {results['total_products'][prod]} / 需求 {products[prod]['demand']}")
        st.write(f"总废料长度: {results['total_waste']}")
        st.write(f"平均每根原材料废料长度: {results['total_waste'] / results['total_materials']:.2f}")


if __name__ == "__main__":
    main()
