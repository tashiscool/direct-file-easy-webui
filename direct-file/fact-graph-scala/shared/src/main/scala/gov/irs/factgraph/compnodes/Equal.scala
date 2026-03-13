package gov.irs.factgraph.compnodes

import gov.irs.factgraph.{Expression, FactDictionary, Factual}
import gov.irs.factgraph.definitions.fact.CompNodeConfigTrait
import gov.irs.factgraph.operators.BinaryOperator

object Equal extends CompNodeFactory:
  override val Key: String = "Equal"

  private val operator = EqualOperator()

  def apply(lhs: CompNode, rhs: CompNode): BooleanNode =
    (lhs, rhs) match
      case (left: EnumNode, right: StringNode) =>
        BooleanNode(
          Expression.Binary(
            AsString(left).expr,
            right.expr,
            operator,
          ),
        )
      case (left: StringNode, right: EnumNode) =>
        BooleanNode(
          Expression.Binary(
            left.expr,
            AsString(right).expr,
            operator,
          ),
        )
      case _ =>
        if (lhs.getClass != rhs.getClass)
          throw new UnsupportedOperationException(
            s"cannot compare a ${lhs.getClass.getName} and a ${rhs.getClass.getName}",
          )

        BooleanNode(
          Expression.Binary(
            lhs.expr,
            rhs.expr,
            operator,
          ),
        )

  override def fromDerivedConfig(e: CompNodeConfigTrait)(using Factual)(using
      FactDictionary,
  ): CompNode =
    val children = e.children.toSeq
    val (lhs, rhs) =
      if (children.exists(_.typeName == "Left") || children.exists(_.typeName == "Right")) then
        (
          CompNode.getConfigChildNode(e, "Left"),
          CompNode.getConfigChildNode(e, "Right"),
        )
      else
        val flatChildren = CompNode.getConfigChildNodes(e)
        flatChildren match
          case left :: right :: Nil => (left, right)
          case _ =>
            throw new IllegalArgumentException(
              s"<${e.typeName}> must have exactly two child nodes: $e",
            )

    this(lhs, rhs)

private final class EqualOperator extends BinaryOperator[Boolean, Any, Any]:
  override protected def operation(x: Any, y: Any): Boolean = x == y
