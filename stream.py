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
            generate_patterns(new_pattern, new_remaining,
                              product_keys[1:], pattern_index)

    generate_patterns({prod: 0 for prod in products},
                      raw_material_length, list(products.keys()), len(patterns))

    # 创建优化问题
    prob = LpProblem("Cutting_Stock_Problem", LpMinimize)

    pattern_vars = [LpVariable(f"pattern_{i + 1}", 0, None, LpInteger)
                    for i in range(len(patterns))]

    prob += lpSum(pattern_vars)

    for prod in products:
        prob += lpSum(patterns[i][prod] * pattern_vars[i]
                      for i in range(len(patterns))) >= products[prod]['demand']

    prob.solve()

    # 准备结果
    results = {}

    # 所有可能的切割方案
    df_patterns = pd.DataFrame(pattern_details)
    df_patterns = df_patterns[['pattern_no'] + list(products.keys()) + ['waste']]
    results['patterns'] = df_patterns

    # 优化结果
    results['status'] = LpStatus[prob.status]
    results['total_materials'] = value(prob.objective)

    # 最优方案组合
    optimal_patterns = []
    total_products = {prod: 0 for prod in products}
    total_waste = 0

    for i, var in enumerate(pattern_vars):
        if value(var) > 0:
            pattern = patterns[i]
            times_used = int(value(var))
            waste = raw_material_length - sum(pattern[p] * products[p]['size']
                                              for p in products)

            pattern_info = {
                'pattern_no': i + 1,
                'details': {prod: pattern[prod] for prod in products},
                'waste': waste,
                'times_used': times_used
            }
            optimal_patterns.append(pattern_info)

            for prod in products:
                total_products[prod] += pattern[prod] * times_used
            total_waste += waste * times_used

    results['optimal_patterns'] = optimal_patterns
    results['total_products'] = total_products
    results['total_waste'] = total_waste
    results['avg_waste'] = total_waste / value(prob.objective)

    return results


def main():
    st.title('下料优化计算器')
    st.write('这是一个帮助你优化下料方案选择的工具')

    # 输入原材料长度
    raw_material_length = st.number_input('请输入原材料长度', min_value=1, value=100)

    # 产品信息输入
    st.subheader('产品信息')
    col1, col2 = st.columns(2)

    with col1:
        num_products = st.number_input('请输入产品种类数量', min_value=1, max_value=10, value=3)

    products = {}
    for i in range(num_products):
        st.write(f'产品 {chr(65 + i)}')
        col1, col2 = st.columns(2)
        with col1:
            size = st.number_input(f'产品{chr(65 + i)}长度', min_value=1, value=20 + i * 10, key=f'size_{i}')
        with col2:
            demand = st.number_input(f'产品{chr(65 + i)}需求量', min_value=1, value=80 + i * 20, key=f'demand_{i}')
        products[chr(65 + i)] = {'size': size, 'demand': demand}

    if st.button('计算优化方案'):
        results = cutting_stock_optimization(products, raw_material_length)

        st.subheader('所有可能的切割方案')
        st.dataframe(results['patterns'])

        st.subheader('优化结果')
        st.write(f"计算状态: {results['status']}")
        st.write(f"需要使用的原材料总数: {results['total_materials']} 根")

        st.subheader('最优方案组合')
        for pattern in results['optimal_patterns']:
            st.write(f"\n方案 {pattern['pattern_no']}:")
            for prod, count in pattern['details'].items():
                st.write(f"{prod}产品数量: {count}")
            st.write(f"废料长度: {pattern['waste']}")
            st.write(f"使用次数: {pattern['times_used']}")

        st.subheader('生产统计')
        for prod, count in results['total_products'].items():
            st.write(f"{prod}产品: 实际生产 {count} / 需求 {products[prod]['demand']}")
        st.write(f"总废料长度: {results['total_waste']}")
        st.write(f"平均每根原材料废料长度: {results['avg_waste']:.2f}")


if __name__ == '__main__':
    main()
