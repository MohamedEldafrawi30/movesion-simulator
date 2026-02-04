"""Core simulation engine for business model calculations."""

from dataclasses import asdict
from typing import Any

from .tiers import TierCalculator
from .types import (
    MonthlyResult,
    SimulationKPIs,
    SimulationResult,
)


class SimulationEngine:
    """
    Business model simulation engine.
    
    Calculates costs, revenues, and profitability projections based on
    scenario parameters and pricing plan configuration.
    """
    
    def __init__(self, pricing_plan: dict[str, Any]):
        """
        Initialize the simulation engine with a pricing plan.
        
        Args:
            pricing_plan: Complete pricing plan configuration dictionary
        """
        self.pricing_plan = pricing_plan
        self.tier_calculator = TierCalculator()
        
        # Pre-index event fees for faster lookup
        self._event_fees_map = {
            e["key"]: e for e in pricing_plan.get("event_fees", [])
        }
        
        # Pre-index optional features
        self._optional_features = pricing_plan.get("optional_features", {})
    
    def simulate(self, scenario: dict[str, Any]) -> SimulationResult:
        """
        Run a complete simulation for the given scenario.
        
        Args:
            scenario: Scenario configuration dictionary
            
        Returns:
            SimulationResult containing monthly projections and KPIs
        """
        # Extract scenario parameters
        months = int(scenario["horizon_months"])
        adoption = scenario["adoption"]
        usage = scenario["usage"]
        commercial = scenario["commercial"]
        toggles = scenario["toggles"]
        ops = scenario.get("ops_assumptions", {})
        issuance = scenario.get("issuance", {})
        
        # Parse adoption parameters
        start_active = float(adoption["start_active_cards"])
        net_adds = float(adoption.get("monthly_net_adds", 0.0))
        churn_rate = float(adoption.get("churn_rate", 0.0))
        
        # Parse usage parameters
        spend_per_active = float(usage["spend_per_active_card_month"])
        in_app_share = float(usage["in_app_share"])
        avg_ticket = float(usage["avg_ticket"])
        ecom_share = float(usage["ecom_share"])
        three_ds_attempt_rate = float(usage.get("three_ds_attempt_rate", 1.0))
        eea_share = float(usage.get("eea_share", 0.95))
        auth_multiplier = float(usage.get("auth_multiplier", 1.0))
        
        # Parse commercial parameters
        partner_fee_pct = float(commercial["partner_fee_pct"])
        interchange_pct = float(commercial["interchange_pct"])
        
        # Parse B2B parameters
        b2b = commercial["b2b"]
        companies = float(b2b.get("companies", 1))
        platform_fee_company_month = float(b2b.get("platform_fee_company_month", 0.0))
        employee_fee_month = float(b2b.get("employee_fee_month", 0.0))
        b2b_mode = b2b.get("mode", "given")
        target = b2b.get("target", {"type": "breakeven", "months": 12})
        target_months = int(target.get("months", 12))
        target_type = target.get("type", "breakeven")
        
        # Parse issuance parameters
        physical_share = float(issuance.get("physical_share_issued", 0.0))
        issued_equals_net_adds = bool(issuance.get("issued_equals_net_adds", True))
        
        # Pre-compute one-off fees by month (from optional features)
        one_offs_by_month = self._compute_one_offs(months, toggles)
        
        # Compute fixed monthly total
        fixed_monthly_total = self._compute_fixed_monthly(toggles)
        
        # Get variable pricing config
        variable = self.pricing_plan.get("variable_monthly", {})
        
        # Run monthly simulation
        rows: list[MonthlyResult] = []
        active = start_active
        cumulative_profit = 0.0
        
        for m in range(1, months + 1):
            # Calculate churn and new users
            churned = active * churn_rate
            active = max(0.0, active - churned + net_adds)
            
            # Calculate issuance
            issued = net_adds if issued_equals_net_adds else 0.0
            issued = max(0.0, issued)
            issued_physical = issued * physical_share
            issued_virtual = issued - issued_physical
            
            # Calculate spend and transactions
            total_spend = active * spend_per_active
            in_app_spend = total_spend * in_app_share
            
            tx = 0.0 if avg_ticket <= 0 else (total_spend / avg_ticket) * auth_multiplier
            eea_auth = tx * eea_share
            non_eea_auth = tx - eea_auth
            ecom_tx = tx * ecom_share
            three_ds_attempts = ecom_tx * three_ds_attempt_rate
            
            # Calculate revenues
            partner_rev = in_app_spend * partner_fee_pct
            interchange_rev = total_spend * interchange_pct
            
            # Calculate costs - active cards
            active_cards_config = variable.get("active_cards", {})
            active_cost = self.tier_calculator.apply_tiers(
                active, active_cards_config.get("tiers", [])
            )
            
            # Calculate costs - authorizations (EEA and non-EEA)
            auth_config = variable.get("authorizations", {})
            eea_tiers = auth_config.get("eea", {}).get("tiers", [])
            non_eea_tiers = auth_config.get("non_eea", {}).get("tiers", [])
            
            auth_cost = (
                self.tier_calculator.apply_tiers(eea_auth, eea_tiers) +
                self.tier_calculator.apply_tiers(non_eea_auth, non_eea_tiers)
            )
            
            # Calculate costs - 3DS
            three_ds_config = variable.get("three_ds", {})
            three_ds_cost = self.tier_calculator.apply_tiers(
                three_ds_attempts, three_ds_config.get("tiers", [])
            )
            
            fixed_cost = fixed_monthly_total
            one_off = one_offs_by_month.get(m, 0.0)
            
            # Calculate event-based costs
            event_cost = self._compute_event_costs(
                toggles, ops, issued, issued_physical, tx, active, churned
            )
            
            # Calculate physical card costs
            physical_cost = self._compute_physical_costs(
                toggles, issued_physical
            )
            
            # Aggregate costs and revenues
            costs_excl_b2b = (
                fixed_cost + one_off + active_cost + auth_cost +
                three_ds_cost + event_cost + physical_cost
            )
            rev_excl_b2b = partner_rev + interchange_rev
            
            # Calculate B2B revenue (placeholder if solving)
            if b2b_mode == "given":
                b2b_rev = companies * platform_fee_company_month + active * employee_fee_month
            else:
                b2b_rev = 0.0  # Will be recalculated after solving
            
            total_rev = rev_excl_b2b + b2b_rev
            profit = total_rev - costs_excl_b2b
            cumulative_profit += profit
            
            rows.append(MonthlyResult(
                month=m,
                active_cards=active,
                issued_cards=issued,
                issued_physical=issued_physical,
                issued_virtual=issued_virtual,
                total_spend=total_spend,
                in_app_spend=in_app_spend,
                tx_count=tx,
                eea_auth=eea_auth,
                non_eea_auth=non_eea_auth,
                three_ds_attempts=three_ds_attempts,
                rev_partner=partner_rev,
                rev_interchange=interchange_rev,
                rev_b2b=b2b_rev,
                cost_fixed=fixed_cost,
                cost_oneoff=one_off,
                cost_active_cards=active_cost,
                cost_auth=auth_cost,
                cost_3ds=three_ds_cost,
                cost_events=event_cost,
                cost_physical=physical_cost,
                total_revenue=total_rev,
                total_costs=costs_excl_b2b,
                profit=profit,
                cumulative_profit=cumulative_profit,
                costs_excl_b2b=costs_excl_b2b,
                rev_excl_b2b=rev_excl_b2b,
            ))
        
        # Solve B2B employee fee if requested
        required_employee_fee = None
        if b2b_mode == "solve_employee_fee":
            required_employee_fee = self._solve_employee_fee(
                rows, companies, platform_fee_company_month,
                target_months, target_type, target
            )
            
            # Recalculate with solved fee
            cumulative_profit = 0.0
            for row in rows:
                row.rev_b2b = (
                    companies * platform_fee_company_month +
                    row.active_cards * required_employee_fee
                )
                row.total_revenue = row.rev_excl_b2b + row.rev_b2b
                row.profit = row.total_revenue - row.costs_excl_b2b
                cumulative_profit += row.profit
                row.cumulative_profit = cumulative_profit
        
        # Calculate KPIs
        kpis = self._calculate_kpis(rows, months, required_employee_fee)
        
        return SimulationResult(
            rows=rows,
            kpis=kpis,
            scenario_name=scenario.get("name", "Unnamed Scenario"),
            pricing_plan_id=self.pricing_plan.get("id", "unknown"),
        )
    
    def _compute_one_offs(
        self, months: int, toggles: dict[str, Any]
    ) -> dict[int, float]:
        """Compute one-off fees by month from optional features."""
        one_offs_by_month: dict[int, float] = {}
        
        # Process optional features with setup costs
        for key, feature in self._optional_features.items():
            toggle_key = feature.get("key", key)
            if toggles.get(toggle_key, feature.get("enabled_by_default", False)):
                setup_cost = float(feature.get("setup", 0))
                if setup_cost > 0:
                    # Apply in month 1
                    one_offs_by_month[1] = one_offs_by_month.get(1, 0.0) + setup_cost
        
        return one_offs_by_month
    
    def _compute_fixed_monthly(self, toggles: dict[str, Any]) -> float:
        """Compute total fixed monthly fees."""
        total = 0.0
        
        # Fixed monthly fees
        for item in self.pricing_plan.get("fixed_monthly", []):
            key = item["key"]
            # Mandatory fees are always included, others check toggles
            if item.get("mandatory", False) or toggles.get(key, item.get("enabled_by_default", False)):
                total += float(item["amount"])
        
        # Monthly costs from optional features
        for key, feature in self._optional_features.items():
            toggle_key = feature.get("key", key)
            if toggles.get(toggle_key, feature.get("enabled_by_default", False)):
                monthly_cost = float(feature.get("monthly", 0))
                total += monthly_cost
        
        return total
    
    def _compute_event_costs(
        self,
        toggles: dict[str, Any],
        ops: dict[str, Any],
        issued: float,
        issued_physical: float,
        tx: float,
        active: float,
        churned: float,
    ) -> float:
        """Compute event-based costs."""
        event_fees = toggles.get("event_fees", {})
        cost = 0.0
        
        def is_enabled(key: str) -> bool:
            fee_config = self._event_fees_map.get(key, {})
            # Mandatory fees are always enabled
            if fee_config.get("mandatory", False):
                return True
            return event_fees.get(
                key,
                fee_config.get("enabled_by_default", False)
            )
        
        # Card issuance fee (mandatory)
        if "card_issue" in self._event_fees_map:
            cost += issued * float(self._event_fees_map["card_issue"]["amount"])
        
        # Plastic personalization (physical only)
        if issued_physical > 0 and is_enabled("plastic_personalization"):
            if "plastic_personalization" in self._event_fees_map:
                cost += issued_physical * float(
                    self._event_fees_map["plastic_personalization"]["amount"]
                )
        
        # KYC attempts
        if issued > 0 and is_enabled("kyc_attempt"):
            if "kyc_attempt" in self._event_fees_map:
                kyc_rate = float(ops.get("kyc_attempts_per_new_user", 1.0))
                cost += issued * kyc_rate * float(
                    self._event_fees_map["kyc_attempt"]["amount"]
                )
        
        # Document confirmations
        if issued > 0 and is_enabled("account_documents"):
            if "account_documents" in self._event_fees_map:
                doc_rate = float(ops.get("doc_confirm_rate_per_new_user", 0.0))
                cost += issued * doc_rate * float(
                    self._event_fees_map["account_documents"]["amount"]
                )
        
        # Disputes
        if is_enabled("dispute") and "dispute" in self._event_fees_map:
            dispute_rate = float(ops.get("dispute_rate_per_tx", 0.0))
            cost += tx * dispute_rate * float(
                self._event_fees_map["dispute"]["amount"]
            )
        
        # SMS notifications
        if is_enabled("sms") and "sms" in self._event_fees_map:
            sms_rate = float(ops.get("sms_per_active_user_month", 0.0))
            cost += active * sms_rate * float(self._event_fees_map["sms"]["amount"])
        
        # PIN changes
        if is_enabled("pin_change") and "pin_change" in self._event_fees_map:
            pin_rate = float(ops.get("pin_changes_per_active_user_month", 0.0))
            cost += active * pin_rate * float(
                self._event_fees_map["pin_change"]["amount"]
            )
        
        # Account closures
        if is_enabled("account_closure") and "account_closure" in self._event_fees_map:
            closure_rate = float(ops.get("closures_per_churned_user", 0.0))
            cost += churned * closure_rate * float(
                self._event_fees_map["account_closure"]["amount"]
            )
        
        return cost
    
    def _compute_physical_costs(
        self, toggles: dict[str, Any], issued_physical: float
    ) -> float:
        """Compute physical card manufacturing and delivery costs."""
        cost = 0.0
        
        if issued_physical <= 0:
            return cost
        
        physical_config = self.pricing_plan.get("physical_cards", {})
        
        # Manufacturing cost
        if toggles.get("physical_manufacturing", False):
            mfg_config = physical_config.get("manufacturing", {})
            tiers = mfg_config.get("tiers", [])
            
            price = 0.0
            for tier in tiers:
                min_batch = tier.get("min_batch", tier.get("min", 0))
                max_batch = tier.get("max_batch", tier.get("max"))
                if issued_physical >= min_batch and (max_batch is None or issued_physical <= max_batch):
                    price = float(tier["price"])
                    break
            
            # If below minimum tier, use first tier price
            if price == 0.0 and tiers:
                price = float(tiers[0]["price"])
            
            cost += issued_physical * price
        
        # Delivery cost
        if toggles.get("physical_delivery", False):
            delivery_config = physical_config.get("delivery", {})
            methods = delivery_config.get("methods", [])
            default_method = delivery_config.get("default_method", "dhl_tracked")
            method_key = toggles.get("delivery_method", default_method)
            
            method = next(
                (m for m in methods if m["key"] == method_key),
                methods[0] if methods else None
            )
            
            if method:
                cost += issued_physical * float(method["price"])
        
        return cost
    
    def _solve_employee_fee(
        self,
        rows: list[MonthlyResult],
        companies: float,
        platform_fee_company_month: float,
        target_months: int,
        target_type: str,
        target: dict[str, Any],
    ) -> float:
        """Solve for the required employee fee to meet the target."""
        horizon = min(target_months, len(rows))
        
        total_costs = sum(r.costs_excl_b2b for r in rows[:horizon])
        total_rev = sum(r.rev_excl_b2b for r in rows[:horizon])
        total_active_months = sum(r.active_cards for r in rows[:horizon])
        platform_component = companies * platform_fee_company_month * horizon
        
        # Determine target profit
        target_profit_total = 0.0
        if target_type == "profit":
            target_profit_total = float(target.get("amount", 0.0))
        elif target_type == "margin":
            # Margin on total revenue (approximation)
            margin = float(target.get("amount", 0.0))
            target_profit_total = total_rev * margin
        
        # Calculate required B2B revenue
        needed_b2b_total = (total_costs - total_rev) + target_profit_total - platform_component
        
        # Solve for employee fee
        if total_active_months <= 0:
            return 0.0
        
        return max(0.0, needed_b2b_total / total_active_months)
    
    def _calculate_kpis(
        self,
        rows: list[MonthlyResult],
        months: int,
        required_employee_fee: float | None,
    ) -> SimulationKPIs:
        """Calculate key performance indicators."""
        # Find breakeven month - must go from negative to positive
        # Not just "first month where cumulative >= 0"
        breakeven_month = None
        was_negative = False
        
        for r in rows:
            if r.cumulative_profit < -0.01:  # Small threshold for floating point
                was_negative = True
            elif was_negative and r.cumulative_profit >= 0:
                # Transitioned from negative to positive/zero
                breakeven_month = r.month
                break
        
        # If never went negative but profit is positive, no breakeven needed
        # If always at zero (solver found exact breakeven fee), show None
        
        # Calculate yearly profits
        profit_year1 = sum(r.profit for r in rows[:12])
        profit_year2 = sum(r.profit for r in rows[12:24]) if months >= 24 else None
        profit_year3 = sum(r.profit for r in rows[24:36]) if months >= 36 else None
        
        # Calculate totals
        total_revenue = sum(r.total_revenue for r in rows)
        total_costs = sum(r.total_costs for r in rows)
        total_profit = sum(r.profit for r in rows)
        avg_monthly_profit = total_profit / len(rows) if rows else 0.0
        
        # Determine profit status and if solver was used
        is_solved_breakeven = required_employee_fee is not None
        
        # Check if profit is essentially zero (balanced state from solver)
        if abs(total_profit) < 1.0:  # Within €1 tolerance
            profit_status = "balanced"
        elif total_profit > 0:
            profit_status = "profitable"
        else:
            profit_status = "loss"
        
        # Calculate ROI
        roi_percent = None
        if total_costs > 0:
            roi_percent = (total_profit / total_costs) * 100
        
        return SimulationKPIs(
            breakeven_month=breakeven_month,
            profit_year1=profit_year1,
            profit_year2=profit_year2,
            profit_year3=profit_year3,
            required_employee_fee_month=required_employee_fee,
            total_revenue=total_revenue,
            total_costs=total_costs,
            total_profit=total_profit,
            avg_monthly_profit=avg_monthly_profit,
            roi_percent=roi_percent,
            profit_status=profit_status,
            is_solved_breakeven=is_solved_breakeven,
        )
    
    def to_dict(self, result: SimulationResult) -> dict[str, Any]:
        """Convert simulation result to dictionary format for API response."""
        return {
            "rows": [asdict(r) for r in result.rows],
            "kpis": asdict(result.kpis),
            "scenario_name": result.scenario_name,
            "pricing_plan_id": result.pricing_plan_id,
        }
