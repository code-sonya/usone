from django.db import connection

def show_stock_sql(productType):
    query = '''
        select main.productId as productId
            , main.sizeId as sizeId
            , main.modelName as modelName
            , main.size as size
            , main.sumQuantity as sumQuantity
            , case
                when m2.typeName='입고' then m2.quantity
                when m2.typeName='출고' then m2.quantity * -1
                else 0
            end as lastQuantity
        from (
            select p.productId as productId
                , p.modelName as modelName
                , s.sizeId as sizeId
                , s.size as size
                , sum(
                    case
                        when m.typeName='입고' then m.quantity
                        when m.typeName='출고' then m.quantity * -1
                        else 0
                    end
                ) as sumQuantity
                , max(m.createdDatetime) as lastDatetime
            
            from daesungwork_product as p
            
            left join daesungwork_type as t
                on p.typeName_id = t.typeId
            left join daesungwork_size as s
                on p.productId = s.productId_id
            left join daesungwork_stockmanagement as m
                on p.productId = m.productName_id
                and s.sizeId = m.sizeName_id
            
            where p.productStatus = 'Y'
                and t.typeName="''' + productType + '''"
            
            group by p.productId, p.modelName, s.sizeId, s.size
        ) as main
        
        left join daesungwork_stockmanagement as m2
            on main.productId = m2.productName_id
            and main.sizeId = m2.sizeName_id
            and main.lastDatetime = m2.createdDateTime;
        '''

    with connection.cursor() as cursor:
        cursor.execute(query)
        row = cursor.fetchall()

    return row