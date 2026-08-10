from __future__ import annotations

from typing import Dict, Any, List


class TitlePlanner:

    """
    标题策略规划器

    功能：
    1. 分析商品核心身份
    2. 判断标题必须包含的信息
    3. 根据75字符限制排序关键词价值

    不生成最终标题
    """


    @staticmethod
    def plan(
        product_knowledge: Dict[str, Any]
    ) -> Dict[str, Any]:


        identity = product_knowledge.get(
            "identity",
            {}
        )

        relationship = product_knowledge.get(
            "relationship",
            {}
        )

        facts = product_knowledge.get(
            "facts",
            {}
        )

        features = product_knowledge.get(
            "features",
            {}
        )


        return {

            "main_product":
                TitlePlanner.get_main_product(
                    identity
                ),
        
        
            "search_terms":
                TitlePlanner.get_search_terms(
                    product_knowledge
                ),
        
        
            "features":
                TitlePlanner.get_features(
                    product_knowledge
                ),
        
        
            "compatibility":
                TitlePlanner.get_compatibility(
                    relationship
                ),
        
        
            "avoid":
                TitlePlanner.get_avoid_terms(
                    identity
                ),
        
        }


    @staticmethod
    def get_main_product(identity):
    
        result=[]
    
    
        product_name = identity.get(
            "product_name",
            ""
        )
    
    
        if product_name:
            result.append(product_name)
    
    
        return result
    @staticmethod
    def get_features(product_knowledge):
    
        result=[]
    
    
        classification = product_knowledge.get(
            "feature_classification",
            {}
        )
    
    
        design = classification.get(
            "design_features",
            []
        )
    
    
        functional = classification.get(
            "functional_features",
            []
        )
    
    
        result.extend(
            design[:3]
        )
    
    
        result.extend(
            functional[:2]
        )
    
    
        blocked_features=[
            "start washing machine",
            "protects extruder",
            "enhances heat retention"
        ]
    
    
        filtered=[]
    
    
        for item in result:
    
            text = str(item).strip()
    
            if not text:
                continue
    
    
            if text.lower() in blocked_features:
                continue
    
    
            filtered.append(text)
    
    
        return filtered[:5]

    @staticmethod
    def get_features(product_knowledge):
    
        result=[]
    
    
        classification = product_knowledge.get(
            "feature_classification",
            {}
        )
    
    
        design = classification.get(
            "design_features",
            []
        )
    
    
        functional = classification.get(
            "functional_features",
            []
        )
    
    
        result.extend(
            design[:3]
        )
    
    
        result.extend(
            functional[:2]
        )
        blocked_features=[
        "start washing machine",
        "protects extruder",
        "enhances heat retention"
    ]
    
        return result[:5]
    @staticmethod
    def get_compatibility(relationship):
    
        brands = relationship.get(
            "brands",
            []
        )
    
    
        if brands:
    
            return [
                "Compatible with "
                + brands[0]
            ]
    
    
        return []
    @staticmethod
    def get_avoid_terms(identity):
    
        category = identity.get(
            "category",
            ""
        )
    
    
        if not category:
    
            return []
    
    
        avoid_terms=[]
    
    
        if category:
    
            avoid_terms.append(category)
    
    
        category_lower = category.lower()
    
    
        if "parts" in category_lower:
    
            avoid_terms.append(category)
    
    
        if "appliances" in category_lower:
    
            avoid_terms.append(category)
    
    
        return list(
            set(avoid_terms)
        )
