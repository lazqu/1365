"""
1365 자원봉사 2단계 파이프라인 모듈 (volunteer_search.py)
[1단계] fetch_all_dataframe(): 데이터 수집 (Data Ingestion)
[2단계] filter_volunteers(df, ...): 순수 필터링/가공 (Data Filtering)
"""

import pandas as pd
import xml.etree.ElementTree as ET
from area_mapper import get_area_code, get_location_name
from fetch_volunteer_data import fetch_data, xml_to_dict

def fetch_all_dataframe(operation="getVltrSearchWordList", num_of_rows=10000) -> pd.DataFrame:
    """
    [1단계: 수집] 1365 API 전체 데이터를 수집하여 raw DataFrame을 반환합니다.
    """
    xml_str = fetch_data(operation=operation, params={"numOfRows": str(num_of_rows), "pageNo": "1"})
    if not xml_str:
        return pd.DataFrame()
        
    root = ET.fromstring(xml_str)
    items = []
    for item_node in root.findall(".//items/item"):
        items.append(xml_to_dict(item_node))
        
    df = pd.DataFrame(items)
    if not df.empty and 'locationName' not in df.columns:
        df['locationName'] = df.apply(lambda row: get_location_name(row.get('sidoCd'), row.get('gugunCd'), row.get('nanmmbyNm', '')), axis=1)
        
    return df

def filter_volunteers(
    df: pd.DataFrame,
    recruiting_only: bool = False,
    adult_posbl: bool = None,
    youth_posbl: bool = None,
    locations = None,
    include_keywords = None,
    exclude_keywords = None,
    target_date: str = None,
    sort_by: str = None,
    ascending: bool = True
) -> pd.DataFrame:
    """
    [2단계: 필터링] 수집된 DataFrame(df)을 입력받아 지정된 조건들로 가공/필터링하는 순수 함수입니다.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    filtered = df.copy()

    # 1. 모집중 여부
    if recruiting_only and 'progrmSttusSe' in filtered.columns:
        filtered = filtered[filtered['progrmSttusSe'] == '2']

    # 2. 성인 가능 여부
    if adult_posbl is not None and 'adultPosblAt' in filtered.columns:
        target_val = 'Y' if adult_posbl else 'N'
        filtered = filtered[filtered['adultPosblAt'] == target_val]

    # 3. 청소년 가능 여부
    if youth_posbl is not None and 'yngbgsPosblAt' in filtered.columns:
        target_val = 'Y' if youth_posbl else 'N'
        filtered = filtered[filtered['yngbgsPosblAt'] == target_val]

    # 4. 지역 OR 조건
    if locations:
        if isinstance(locations, str):
            locations = [locations]
            
        target_sidos = set()
        target_guguns = set()
        location_terms = []

        for loc in locations:
            s_code, g_code = get_area_code(loc)
            if s_code: target_sidos.add(str(s_code))
            if g_code: target_guguns.add(str(g_code))
            location_terms.append(loc)

        def matches_location(row):
            s_cd = str(row.get('sidoCd', ''))
            g_cd = str(row.get('gugunCd', ''))
            loc_name = str(row.get('locationName', '')) + " " + str(row.get('nanmmbyNm', ''))
            
            if s_cd in target_sidos or g_cd in target_guguns:
                return True
            for term in location_terms:
                if term in loc_name:
                    return True
            return False

        filtered = filtered[filtered.apply(matches_location, axis=1)]

    # 5. 특정 키워드 포함
    if include_keywords:
        if isinstance(include_keywords, str):
            include_keywords = [include_keywords]

        def matches_includes(row):
            text = f"{row.get('progrmSj', '')} {row.get('nanmmbyNm', '')} {row.get('actPlace', '')}"
            return any(kwd in text for kwd in include_keywords)

        filtered = filtered[filtered.apply(matches_includes, axis=1)]

    # 6. 특정 키워드 미포함
    if exclude_keywords:
        if isinstance(exclude_keywords, str):
            exclude_keywords = [exclude_keywords]

        def matches_excludes(row):
            text = f"{row.get('progrmSj', '')} {row.get('nanmmbyNm', '')} {row.get('actPlace', '')}"
            return not any(kwd in text for kwd in exclude_keywords)

        filtered = filtered[filtered.apply(matches_excludes, axis=1)]

    # 7. 특정 날짜 포함
    if target_date:
        clean_date = str(target_date).replace("-", "").replace(".", "").strip()
        def matches_date(row):
            bgnde = str(row.get('progrmBgnde', ''))
            endde = str(row.get('progrmEndde', ''))
            if bgnde and endde:
                return bgnde <= clean_date <= endde
            return True

        filtered = filtered[filtered.apply(matches_date, axis=1)]

    # 8. 다중 칼럼 정렬 지원
    if sort_by:
        if isinstance(sort_by, str):
            sort_by = [sort_by]
        
        valid_cols = [col for col in sort_by if col in filtered.columns]
        if valid_cols:
            filtered = filtered.sort_values(by=valid_cols, ascending=ascending)

    return filtered.reset_index(drop=True)

if __name__ == "__main__":
    print("=== 1단계: 최초 1회 전체 수집 ===")
    df_raw = fetch_all_dataframe()
    print(f"원천 데이터 수집 완료: 총 {len(df_raw)}건")

    print("\n=== 2단계: 수집된 df_raw로 네트워크 0번 재호출 필터링 ===")
    df_seoul = filter_volunteers(df_raw, locations="서울", adult_posbl=True)
    print(f"서울 성인 가능 봉사: {len(df_seoul)}건")
