def calculate_next_station(current_station_id: int):
    """
    模拟路径规划算法
    实际项目中应基于图算法 (Dijkstra) 或查询数据库中的路由规则表
    """
    # 简单 Mock: 如果当前是 1(上海)，下一站去 2(上海分拨)
    if current_station_id == 1:
        return 2
    # 如果当前是 2(上海分拨)，下一站去 3(北京分拨)
    if current_station_id == 2:
        return 3
    return None